"""
Automax next execution engine.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
import logging
from pathlib import Path
import re
from threading import Lock
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional

from automax.core.inventory import Inventory
from automax.core.models import ExecutionContext, NodeStatus, PluginResult, Target
from automax.core.secrets import SecretManager
from automax.core.ssh import SshSessionManager
from automax.core.state import StateStore
from automax.core.templating import render_mapping, render_value
from automax.core.yaml_loader import load_yaml_file
from automax.plugins.registry import PluginRegistry, build_builtin_registry


class AutomaxError(ValueError):
    """Raised for user-facing Automax errors."""


class AutomaxEngine:
    """Load external definitions, validate and execute one job."""

    def __init__(
        self,
        *,
        plugin_registry: Optional[PluginRegistry] = None,
        secret_manager: Optional[SecretManager] = None,
        ssh_manager: Optional[SshSessionManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.plugin_registry = plugin_registry or build_builtin_registry()
        self.secret_manager = secret_manager or SecretManager()
        self.ssh_manager = ssh_manager or SshSessionManager()
        self.logger = logger or logging.getLogger("automax")
        self._output_lock = Lock()
        self._print_lock = Lock()

    def run(
        self,
        *,
        job_path: str,
        inventory_path: str,
        vars_path: str | None = None,
        secrets_path: str | None = None,
        state_dir: str = ".automax/runs",
        run_id: str | None = None,
        dry_run: bool = False,
        plan_only: bool = False,
        from_node: str | None = None,
        limit: Iterable[str] = (),
        exclude: Iterable[str] = (),
        tags: Iterable[str] = (),
        skip_tags: Iterable[str] = (),
        cli_vars: Optional[Dict[str, Any]] = None,
        extra_plugin_paths: Iterable[str] = (),
    ) -> int:
        """Execute a new run from external YAML files."""
        registry = self.plugin_registry
        if extra_plugin_paths:
            registry.load_from_paths(extra_plugin_paths)

        documents = self._load_documents(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
        )
        secrets = self.secret_manager.resolve_all(documents["secrets"])
        variables = self._merge_variables(
            documents["vars"], documents["job"].get("vars", {}), cli_vars or {}
        )
        context = {"vars": variables, "secrets": secrets}
        inventory = Inventory(documents["inventory"], context)
        job = documents["job"]
        self.validate_job(job)

        run_id = run_id or self._build_run_id(job)
        store = StateStore(state_dir, run_id)
        store.create_run(
            job_path=str(Path(job_path).expanduser()),
            inventory_path=str(Path(inventory_path).expanduser()),
            vars_path=str(Path(vars_path).expanduser()) if vars_path else None,
            secrets_path=str(Path(secrets_path).expanduser()) if secrets_path else None,
            metadata={
                "dry_run": dry_run,
                "from": from_node,
                "limit": list(limit),
                "tags": list(tags),
                "skip_tags": list(skip_tags),
            },
        )
        store.record_event("job_started", payload={"job": self._job_name(job)})

        try:
            plan = self._build_plan(
                job,
                inventory,
                limit=limit,
                exclude=exclude,
                tags=tags,
                skip_tags=skip_tags,
            )
            if plan_only:
                self._print_plan(run_id, plan)
                store.update_run_status(NodeStatus.SUCCESS)
                return 0

            rc = self._execute_plan(
                job=job,
                plan=plan,
                store=store,
                run_id=run_id,
                dry_run=dry_run,
                variables=variables,
                secrets=secrets,
                from_node=from_node,
            )
            store.update_run_status(NodeStatus.SUCCESS if rc == 0 else NodeStatus.FAILED)
            store.record_event("job_finished", payload={"rc": rc})
            print(f"Run ID: {run_id}")
            if rc != 0:
                print(f"Resume: automax resume {run_id} --state-dir {state_dir}")
            return rc
        except Exception as exc:
            store.update_run_status(NodeStatus.FAILED)
            store.record_event("job_failed", payload={"error": str(exc)})
            raise

    def resume(
        self,
        *,
        run_id: str,
        state_dir: str = ".automax/runs",
        from_node: str | None = None,
        dry_run: bool = False,
        limit: Iterable[str] = (),
        exclude: Iterable[str] = (),
        tags: Iterable[str] = (),
        skip_tags: Iterable[str] = (),
        cli_vars: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Resume a previous run using paths stored in the run state."""
        store = StateStore(state_dir, run_id)
        run = store.get_run()
        if not run:
            raise AutomaxError(f"run not found: {run_id}")
        from_node = from_node or store.first_failed_node_id()
        if not from_node:
            raise AutomaxError(f"run has no failed checkpoint: {run_id}")
        return self.run(
            job_path=run["job_path"],
            inventory_path=run["inventory_path"],
            vars_path=run.get("vars_path"),
            secrets_path=run.get("secrets_path"),
            state_dir=state_dir,
            run_id=run_id,
            dry_run=dry_run,
            from_node=from_node,
            limit=limit,
            exclude=exclude,
            tags=tags,
            skip_tags=skip_tags,
            cli_vars=cli_vars,
        )

    def validate(
        self,
        *,
        job_path: str,
        inventory_path: str,
        vars_path: str | None = None,
        secrets_path: str | None = None,
        cli_vars: Optional[Dict[str, Any]] = None,
        tags: Iterable[str] = (),
        skip_tags: Iterable[str] = (),
    ) -> None:
        """Validate external YAML files without executing."""
        documents = self._load_documents(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
        )
        secrets = self.secret_manager.resolve_all(documents["secrets"])
        variables = self._merge_variables(
            documents["vars"], documents["job"].get("vars", {}), cli_vars or {}
        )
        inventory = Inventory(documents["inventory"], {"vars": variables, "secrets": secrets})
        job = documents["job"]
        self.validate_job(job)
        self._build_plan(job, inventory, limit=(), exclude=(), tags=tags, skip_tags=skip_tags)

    def validate_job(self, job: Dict[str, Any]) -> None:
        """Validate the canonical three-level job DSL."""
        if job.get("apiVersion") != "automax.io/v1":
            raise AutomaxError("job apiVersion must be 'automax.io/v1'")
        if job.get("kind") != "Job":
            raise AutomaxError("job kind must be 'Job'")
        self._validate_strategy(job.get("strategy"), "job")
        self._validate_failure_policy(job.get("failurePolicy"), "job")
        tasks = job.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise AutomaxError("job requires non-empty tasks list")

        seen_tasks = set()
        for task in tasks:
            task_id = self._require_id(task, "task")
            self._validate_strategy(task.get("strategy"), f"task '{task_id}'")
            self._validate_failure_policy(task.get("failurePolicy"), f"task '{task_id}'")
            self._validate_tags(task.get("tags"), f"task '{task_id}'")
            if task_id in seen_tasks:
                raise AutomaxError(f"duplicate task id: {task_id}")
            seen_tasks.add(task_id)
            steps = task.get("steps")
            if not isinstance(steps, list) or not steps:
                raise AutomaxError(f"task '{task_id}' requires non-empty steps")
            seen_steps = set()
            for step in steps:
                step_id = self._require_id(step, "step")
                self._validate_strategy(step.get("strategy"), f"step '{task_id}:{step_id}'")
                self._validate_failure_policy(step.get("failurePolicy"), f"step '{task_id}:{step_id}'")
                self._validate_tags(step.get("tags"), f"step '{task_id}:{step_id}'")
                if step_id in seen_steps:
                    raise AutomaxError(f"duplicate step id in task '{task_id}': {step_id}")
                seen_steps.add(step_id)
                substeps = step.get("substeps")
                if not isinstance(substeps, list) or not substeps:
                    raise AutomaxError(
                        f"step '{task_id}:{step_id}' requires non-empty substeps"
                    )
                seen_substeps = set()
                for substep in substeps:
                    substep_id = self._require_id(substep, "substep")
                    self._validate_tags(
                        substep.get("tags"), f"substep '{task_id}:{step_id}:{substep_id}'"
                    )
                    if substep_id in seen_substeps:
                        raise AutomaxError(
                            f"duplicate substep id in '{task_id}:{step_id}': {substep_id}"
                        )
                    seen_substeps.add(substep_id)
                    plugin_name = substep.get("use") or substep.get("plugin")
                    if not plugin_name:
                        raise AutomaxError(
                            f"substep '{task_id}:{step_id}:{substep_id}' requires 'use'"
                        )
                    plugin = self.plugin_registry.get(str(plugin_name))
                    params = substep.get("with", substep.get("params", {})) or {}
                    if not isinstance(params, dict):
                        raise AutomaxError(
                            f"substep '{task_id}:{step_id}:{substep_id}' params must be mapping"
                        )
                    plugin.validate(params)

    def _load_documents(self, **paths: str | None) -> Dict[str, Dict[str, Any]]:
        return {
            "job": load_yaml_file(paths["job_path"]),
            "inventory": load_yaml_file(paths["inventory_path"]),
            "vars": load_yaml_file(paths.get("vars_path"), required=False)
            if paths.get("vars_path")
            else {},
            "secrets": load_yaml_file(paths.get("secrets_path"), required=False)
            if paths.get("secrets_path")
            else {},
        }

    @staticmethod
    def _merge_variables(*sources: Dict[str, Any]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for source in sources:
            if not source:
                continue
            values = source.get("vars", source)
            if not isinstance(values, dict):
                raise AutomaxError("vars file/root must be a mapping")
            merged.update(values)
        return merged

    def _build_plan(
        self,
        job: Dict[str, Any],
        inventory: Inventory,
        *,
        limit: Iterable[str],
        exclude: Iterable[str],
        tags: Iterable[str] = (),
        skip_tags: Iterable[str] = (),
    ) -> List[Dict[str, Any]]:
        selected_tags = {str(tag) for tag in tags}
        skipped_tags = {str(tag) for tag in skip_tags}
        plan = []
        for task in job["tasks"]:
            task_selector = task.get("targets", job.get("targets", "all"))
            task_targets = inventory.select(
                task_selector,
                limit=list(limit),
                exclude=list(exclude),
            )
            if not task_targets:
                raise AutomaxError(f"task '{task['id']}' resolved no targets")
            for step in task["steps"]:
                step_selector = step.get("targets", task_selector)
                step_targets = inventory.select(
                    step_selector,
                    limit=list(limit),
                    exclude=list(exclude),
                )
                if not step_targets:
                    raise AutomaxError(
                        f"step '{task['id']}:{step['id']}' resolved no targets"
                    )
                for substep in step["substeps"]:
                    effective_tags = self._effective_tags(job, task, step, substep)
                    if not self._tag_selected(effective_tags, selected_tags, skipped_tags):
                        continue
                    substep_selector = substep.get("targets", step_selector)
                    substep_targets = inventory.select(
                        substep_selector,
                        limit=list(limit),
                        exclude=list(exclude),
                    )
                    if not substep_targets:
                        raise AutomaxError(
                            f"substep '{task['id']}:{step['id']}:{substep['id']}' resolved no targets"
                        )
                    for target in substep_targets:
                        plan.append(
                            {
                                "node_id": self._node_id(task, step, substep),
                                "target": target,
                                "task": task,
                                "step": step,
                                "substep": substep,
                                "tags": tuple(sorted(effective_tags)),
                            }
                        )
        if not plan:
            raise AutomaxError("job plan is empty after target/tag filtering")
        return plan

    def _execute_plan(
        self,
        *,
        job: Dict[str, Any],
        plan: List[Dict[str, Any]],
        store: StateStore,
        run_id: str,
        dry_run: bool,
        variables: Dict[str, Any],
        secrets: Dict[str, Any],
        from_node: str | None,
    ) -> int:
        outputs: Dict[str, Any] = {}
        started = from_node is None
        failed_hosts: set[str] = set()
        stopped_tasks: set[str] = set()
        rc = 0

        stages = self._group_by_stage(plan)
        for stage in stages:
            stage_groups: List[List[Dict[str, Any]]] = []
            for group in stage:
                task = group[0]["task"]
                target = group[0]["target"]
                if task["id"] in stopped_tasks:
                    self._mark_group_skipped(store, group, "skipped by failure policy stop_task")
                    continue
                if target.name in failed_hosts:
                    self._mark_group_skipped(store, group, "skipped by failure policy stop_host")
                    continue
                restart_index = self._restart_index(group, from_node) if from_node else 0
                if from_node and restart_index is not None:
                    started = True
                    if restart_index > 0:
                        self._mark_group_skipped(
                            store,
                            group[:restart_index],
                            f"skipped before restart point {from_node}",
                        )
                    stage_groups.append(group[restart_index:])
                    continue
                if not started:
                    self._mark_group_skipped(
                        store,
                        group,
                        f"skipped before restart point {from_node}",
                    )
                    continue
                stage_groups.append(group)

            if not stage_groups:
                continue

            strategy = self._resolve_strategy(job, stage_groups[0][0]["task"], stage_groups[0][0]["step"])
            results = self._execute_stage(
                job=job,
                groups=stage_groups,
                store=store,
                run_id=run_id,
                dry_run=dry_run,
                variables=variables,
                secrets=secrets,
                outputs=outputs,
                strategy=strategy,
            )
            for group, group_rc, failed_by_exception in results:
                if group_rc == 0:
                    continue
                rc = 1
                policy = self._resolve_failure_policy(job, group[0]["task"], group[0]["step"])
                action_key = "onUnreachable" if failed_by_exception else "onFailure"
                action = str(policy.get(action_key, policy.get("onFailure", "stop_job")))
                target_name = group[0]["target"].name
                task_id = group[0]["task"]["id"]
                if action == "continue":
                    continue
                if action == "stop_host":
                    failed_hosts.add(target_name)
                    if self._max_failed_hosts_reached(failed_hosts, policy):
                        return 1
                    continue
                if action == "stop_task":
                    stopped_tasks.add(task_id)
                    continue
                return 1
        return rc

    def _execute_stage(
        self,
        *,
        job: Dict[str, Any],
        groups: List[List[Dict[str, Any]]],
        store: StateStore,
        run_id: str,
        dry_run: bool,
        variables: Dict[str, Any],
        secrets: Dict[str, Any],
        outputs: Dict[str, Any],
        strategy: Dict[str, Any],
    ) -> List[tuple[List[Dict[str, Any]], int, bool]]:
        mode = strategy["mode"]
        if mode == "serial":
            return [
                self._execute_group_with_connection(
                    job=job,
                    group=group,
                    store=store,
                    run_id=run_id,
                    dry_run=dry_run,
                    variables=variables,
                    secrets=secrets,
                    outputs=outputs,
                )
                for group in groups
            ]

        if mode == "parallel":
            max_parallel = int(strategy.get("max_parallel", len(groups)) or len(groups))
            return self._execute_group_chunks(
                job=job,
                groups=self._chunks(groups, max_parallel),
                store=store,
                run_id=run_id,
                dry_run=dry_run,
                variables=variables,
                secrets=secrets,
                outputs=outputs,
            )

        if mode == "rolling":
            batch_size = int(strategy.get("batch_size", 1) or 1)
            pause = float(strategy.get("pause_between_batches", 0) or 0)
            results: List[tuple[List[Dict[str, Any]], int, bool]] = []
            chunks = list(self._chunks(groups, batch_size))
            for index, chunk in enumerate(chunks):
                results.extend(
                    self._execute_group_chunks(
                        job=job,
                        groups=[chunk],
                        store=store,
                        run_id=run_id,
                        dry_run=dry_run,
                        variables=variables,
                        secrets=secrets,
                        outputs=outputs,
                    )
                )
                if pause > 0 and index < len(chunks) - 1:
                    time.sleep(pause)
            return results

        raise AutomaxError(f"unsupported strategy mode: {mode}")

    def _execute_group_chunks(
        self,
        *,
        job: Dict[str, Any],
        groups: Iterable[List[List[Dict[str, Any]]]],
        store: StateStore,
        run_id: str,
        dry_run: bool,
        variables: Dict[str, Any],
        secrets: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> List[tuple[List[Dict[str, Any]], int, bool]]:
        results: List[tuple[List[Dict[str, Any]], int, bool]] = []
        for chunk in groups:
            with ThreadPoolExecutor(max_workers=len(chunk)) as executor:
                futures = {
                    executor.submit(
                        self._execute_group_with_connection,
                        job=job,
                        group=group,
                        store=store,
                        run_id=run_id,
                        dry_run=dry_run,
                        variables=variables,
                        secrets=secrets,
                        outputs=outputs,
                    ): group
                    for group in chunk
                }
                for future in as_completed(futures):
                    results.append(future.result())
        return results

    def _execute_group_with_connection(
        self,
        *,
        job: Dict[str, Any],
        group: List[Dict[str, Any]],
        store: StateStore,
        run_id: str,
        dry_run: bool,
        variables: Dict[str, Any],
        secrets: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        first = group[0]
        task = first["task"]
        step = first["step"]
        target = first["target"]
        needs_ssh = any(self._substep_needs_ssh(item["substep"]) for item in group)
        try:
            if needs_ssh:
                with self.ssh_manager.connect(target) as ssh_client:
                    group_rc = self._execute_step_group(
                        job=job,
                        group=group,
                        store=store,
                        run_id=run_id,
                        dry_run=dry_run,
                        variables=variables,
                        secrets=secrets,
                        outputs=outputs,
                        ssh_client=ssh_client,
                    )
            else:
                group_rc = self._execute_step_group(
                    job=job,
                    group=group,
                    store=store,
                    run_id=run_id,
                    dry_run=dry_run,
                    variables=variables,
                    secrets=secrets,
                    outputs=outputs,
                    ssh_client=None,
                )
            return group, group_rc, False
        except Exception as exc:
            for item in group:
                store.start_node(
                    node_id=item["node_id"],
                    target=target.name,
                    task_id=task["id"],
                    step_id=step["id"],
                    substep_id=item["substep"]["id"],
                )
                store.finish_node(
                    node_id=item["node_id"],
                    target=target.name,
                    status=NodeStatus.FAILED,
                    rc=1,
                    message=str(exc),
                )
            return group, 1, True

    def _execute_step_group(
        self,
        *,
        job: Dict[str, Any],
        group: List[Dict[str, Any]],
        store: StateStore,
        run_id: str,
        dry_run: bool,
        variables: Dict[str, Any],
        secrets: Dict[str, Any],
        outputs: Dict[str, Any],
        ssh_client: Any,
    ) -> int:
        step_state: Dict[str, Any] = {}
        for item in group:
            task = item["task"]
            step = item["step"]
            substep = item["substep"]
            target = item["target"]
            node_id = item["node_id"]
            store.start_node(
                node_id=node_id,
                target=target.name,
                task_id=task["id"],
                step_id=step["id"],
                substep_id=substep["id"],
            )
            try:
                result = self._execute_substep(
                    job=job,
                    task=task,
                    step=step,
                    substep=substep,
                    target=target,
                    run_id=run_id,
                    dry_run=dry_run,
                    variables=variables,
                    secrets=secrets,
                    outputs=outputs,
                    ssh_client=ssh_client,
                    step_state=step_state,
                )
            except Exception as exc:
                result = PluginResult.failure(message=str(exc))

            with self._output_lock:
                self._register_outputs(outputs, node_id, target.name, substep, result)
            store.finish_node(
                node_id=node_id,
                target=target.name,
                status=NodeStatus.SUCCESS if result.ok else NodeStatus.FAILED,
                changed=result.changed,
                rc=result.rc,
                message=result.message,
                output=self._result_to_mapping(result),
            )
            store.record_event(
                "substep_finished",
                node_id=node_id,
                target=target.name,
                payload={"ok": result.ok, "changed": result.changed, "rc": result.rc},
            )
            status = "OK" if result.ok else "FAILED"
            with self._print_lock:
                print(
                    f"[{status}] {target.name} {node_id} rc={result.rc} {result.message}".rstrip()
                )
            if not result.ok:
                return 1
        return 0

    def _execute_substep(
        self,
        *,
        job: Dict[str, Any],
        task: Dict[str, Any],
        step: Dict[str, Any],
        substep: Dict[str, Any],
        target: Target,
        run_id: str,
        dry_run: bool,
        variables: Dict[str, Any],
        secrets: Dict[str, Any],
        outputs: Dict[str, Any],
        ssh_client: Any,
        step_state: Dict[str, Any],
    ) -> PluginResult:
        effective_vars = deepcopy(variables)
        effective_vars.update(target.vars)
        template_context = {
            "job": job,
            "task": task,
            "step": step,
            "substep": substep,
            "server": target,
            "target": target,
            "vars": effective_vars,
            "outputs": outputs,
            "secrets": secrets,
            "step_state": step_state,
        }
        if not self._is_condition_true(substep.get("when"), template_context):
            return PluginResult.skipped_result("condition evaluated to false")

        rendered_substep = render_mapping(substep, template_context)
        plugin_name = rendered_substep.get("use") or rendered_substep.get("plugin")
        params = rendered_substep.get("with", rendered_substep.get("params", {})) or {}
        plugin = self.plugin_registry.get(str(plugin_name))
        plugin.validate(params)

        context = ExecutionContext(
            run_id=run_id,
            dry_run=dry_run,
            job=job,
            task=task,
            step=step,
            substep=rendered_substep,
            target=target,
            vars=effective_vars,
            outputs=outputs,
            secrets=secrets,
            ssh_client=ssh_client,
            logger=self.logger,
            step_state=step_state,
        )
        if dry_run:
            return plugin.dry_run(params, context)
        return plugin.execute(params, context)

    def _is_condition_true(self, condition: Any, context: Dict[str, Any]) -> bool:
        if condition is None:
            return True
        if isinstance(condition, bool):
            return condition
        rendered = render_value(str(condition), context).strip().lower()
        return rendered not in ("", "0", "false", "no", "none")

    def _register_outputs(
        self,
        outputs: Dict[str, Any],
        node_id: str,
        target_name: str,
        substep: Dict[str, Any],
        result: PluginResult,
    ) -> None:
        result_map = self._result_to_mapping(result)
        outputs.setdefault("nodes", {})[node_id] = result_map
        outputs.setdefault("targets", {}).setdefault(target_name, {}).setdefault("nodes", {})[
            node_id
        ] = result_map
        register = substep.get("register")
        if not register:
            return
        if isinstance(register, str):
            outputs[register] = result_map
            outputs["targets"][target_name][register] = result_map
            return
        if isinstance(register, dict):
            for name, expression in register.items():
                value = self._extract_result_value(result_map, str(expression))
                outputs[name] = value
                outputs["targets"][target_name][name] = value

    @staticmethod
    def _extract_result_value(result: Dict[str, Any], expression: str) -> Any:
        if expression == "stdout.trim":
            return str(result.get("stdout", "")).strip()
        current: Any = result
        for part in expression.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    @staticmethod
    def _result_to_mapping(result: PluginResult) -> Dict[str, Any]:
        return {
            "ok": result.ok,
            "changed": result.changed,
            "skipped": result.skipped,
            "rc": result.rc,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": result.message,
            "data": result.data,
        }

    def _substep_needs_ssh(self, substep: Dict[str, Any]) -> bool:
        plugin_name = substep.get("use") or substep.get("plugin")
        plugin = self.plugin_registry.get(str(plugin_name))
        return bool(plugin.opens_remote_session)

    @staticmethod
    def _group_by_step_target(plan: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        groups: List[List[Dict[str, Any]]] = []
        current_key = None
        for item in plan:
            key = (item["task"]["id"], item["step"]["id"], item["target"].name)
            if key != current_key:
                groups.append([])
                current_key = key
            groups[-1].append(item)
        return groups

    def _group_by_stage(self, plan: List[Dict[str, Any]]) -> List[List[List[Dict[str, Any]]]]:
        stages: List[List[List[Dict[str, Any]]]] = []
        current_key = None
        for group in self._group_by_step_target(plan):
            key = (group[0]["task"]["id"], group[0]["step"]["id"])
            if key != current_key:
                stages.append([])
                current_key = key
            stages[-1].append(group)
        return stages

    def _mark_group_skipped(
        self, store: StateStore, group: List[Dict[str, Any]], message: str
    ) -> None:
        for item in group:
            store.mark_skipped(
                node_id=item["node_id"],
                target=item["target"].name,
                task_id=item["task"]["id"],
                step_id=item["step"]["id"],
                substep_id=item["substep"]["id"],
                message=message,
            )

    def _restart_index(self, group: List[Dict[str, Any]], from_node: str | None) -> int | None:
        if not from_node:
            return 0
        for index, item in enumerate(group):
            if self._matches_restart(item, from_node):
                if from_node == item["node_id"]:
                    return index
                return 0
        return None

    @staticmethod
    def _matches_restart(item: Dict[str, Any], from_node: str) -> bool:
        task_id = item["task"]["id"]
        step_id = item["step"]["id"]
        task_node = f"task.{task_id}"
        step_node = f"{task_node}:step.{step_id}"
        return from_node in (task_node, step_node, item["node_id"])

    @staticmethod
    def _node_id(task: Dict[str, Any], step: Dict[str, Any], substep: Dict[str, Any]) -> str:
        return f"task.{task['id']}:step.{step['id']}:substep.{substep['id']}"

    @staticmethod
    def _require_id(node: Dict[str, Any], label: str) -> str:
        node_id = node.get("id")
        if not node_id or not isinstance(node_id, str):
            raise AutomaxError(f"{label} requires string id")
        if not re.match(r"^[A-Za-z0-9_.-]+$", node_id):
            raise AutomaxError(f"invalid {label} id: {node_id}")
        return node_id

    @staticmethod
    def _job_name(job: Dict[str, Any]) -> str:
        metadata = job.get("metadata", {}) or {}
        return str(metadata.get("name", "job"))

    def _build_run_id(self, job: Dict[str, Any]) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        name = re.sub(r"[^A-Za-z0-9_.-]+", "-", self._job_name(job)).strip("-") or "job"
        return f"{stamp}-{name}-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _print_plan(run_id: str, plan: List[Dict[str, Any]]) -> None:
        print(f"Run ID: {run_id}")
        for item in plan:
            tags = f" tags={','.join(item['tags'])}" if item.get("tags") else ""
            print(f"{item['target'].name} {item['node_id']}{tags}")

    @staticmethod
    def _effective_tags(
        job: Dict[str, Any], task: Dict[str, Any], step: Dict[str, Any], substep: Dict[str, Any]
    ) -> set[str]:
        tags: set[str] = set()
        for node in (job, task, step, substep):
            raw_tags = node.get("tags", []) or []
            if isinstance(raw_tags, str):
                tags.add(raw_tags)
            else:
                tags.update(str(tag) for tag in raw_tags)
        return tags

    @staticmethod
    def _tag_selected(
        effective_tags: set[str], selected_tags: set[str], skipped_tags: set[str]
    ) -> bool:
        if skipped_tags and effective_tags.intersection(skipped_tags):
            return False
        if selected_tags and not effective_tags.intersection(selected_tags):
            return False
        return True

    @staticmethod
    def _validate_tags(tags: Any, label: str) -> None:
        if tags is None:
            return
        if isinstance(tags, str):
            return
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise AutomaxError(f"{label} tags must be a string or list of strings")

    def _resolve_strategy(
        self, job: Dict[str, Any], task: Dict[str, Any], step: Dict[str, Any]
    ) -> Dict[str, Any]:
        strategy: Dict[str, Any] = {"mode": "serial"}
        for node in (job, task, step):
            raw = node.get("strategy")
            if raw:
                strategy.update(raw)
        self._validate_strategy(strategy, "resolved strategy")
        return strategy

    @staticmethod
    def _validate_strategy(strategy: Any, label: str) -> None:
        if strategy is None:
            return
        if not isinstance(strategy, dict):
            raise AutomaxError(f"{label} strategy must be a mapping")
        mode = str(strategy.get("mode", "serial"))
        if mode not in {"serial", "parallel", "rolling"}:
            raise AutomaxError(f"{label} strategy mode must be serial, parallel or rolling")
        for key in ("max_parallel", "batch_size"):
            if key in strategy and int(strategy[key]) < 1:
                raise AutomaxError(f"{label} strategy {key} must be >= 1")
        if "pause_between_batches" in strategy and float(strategy["pause_between_batches"]) < 0:
            raise AutomaxError(f"{label} strategy pause_between_batches must be >= 0")

    def _resolve_failure_policy(
        self, job: Dict[str, Any], task: Dict[str, Any], step: Dict[str, Any]
    ) -> Dict[str, Any]:
        policy: Dict[str, Any] = {
            "onFailure": "stop_job",
            "onUnreachable": "stop_job",
            "maxFailedHosts": 0,
        }
        for node in (job, task, step):
            raw = node.get("failurePolicy")
            if raw:
                policy.update(raw)
        self._validate_failure_policy(policy, "resolved failurePolicy")
        return policy

    @staticmethod
    def _validate_failure_policy(policy: Any, label: str) -> None:
        if policy is None:
            return
        if not isinstance(policy, dict):
            raise AutomaxError(f"{label} failurePolicy must be a mapping")
        allowed = {"stop_job", "stop_task", "stop_host", "continue"}
        for key in ("onFailure", "onUnreachable"):
            if key in policy and str(policy[key]) not in allowed:
                raise AutomaxError(
                    f"{label} failurePolicy {key} must be one of: {', '.join(sorted(allowed))}"
                )
        if "maxFailedHosts" in policy and int(policy["maxFailedHosts"]) < 0:
            raise AutomaxError(f"{label} failurePolicy maxFailedHosts must be >= 0")

    @staticmethod
    def _max_failed_hosts_reached(failed_hosts: set[str], policy: Dict[str, Any]) -> bool:
        limit = int(policy.get("maxFailedHosts", 0) or 0)
        return bool(limit and len(failed_hosts) > limit)

    @staticmethod
    def _chunks(items: List[Any], size: int) -> Iterable[List[Any]]:
        for offset in range(0, len(items), size):
            yield items[offset : offset + size]
