# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Automax next execution engine.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import logging
from pathlib import Path
import re
from threading import Lock
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional

from automax.core.inventory import Inventory, load_inventory_document
from automax.core.job_views import build_job_view
from automax.core.locks import LockManager
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
        skip_successful: bool = False,
        only_failed: bool = False,
        output_format: str = "text",
        lock: bool = False,
        lock_scope: str = "both",
        lock_timeout: float = 0,
    ) -> int:
        """Execute a new run from external YAML files."""
        self._validate_output_format(output_format)
        registry = self.plugin_registry
        if extra_plugin_paths:
            registry.load_from_paths(extra_plugin_paths)

        documents = self._load_documents(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
        )
        secrets = self.secret_manager.resolve_all(
            documents["secrets"],
            base_dir=Path(secrets_path).expanduser().resolve().parent if secrets_path else None,
        )
        variables = self._merge_variables(
            documents["vars"], documents["job"].get("vars", {}), cli_vars or {}
        )
        context = {"vars": variables, "secrets": secrets}
        inventory_document = load_inventory_document(inventory_path, context)
        inventory = Inventory(inventory_document, context)
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
                "skip_successful": skip_successful,
                "only_failed": only_failed,
                "lock": lock,
                "lock_scope": lock_scope,
                "lock_timeout": lock_timeout,
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
                store.update_run_status(NodeStatus.SUCCESS)
                self._print_plan(run_id, plan, output_format=output_format)
                return 0

            lock_manager = LockManager.for_state_dir(state_dir) if lock else None
            acquired_locks = []
            try:
                if lock_manager:
                    acquired_locks = lock_manager.acquire_many(
                        self._lock_names(job, plan, scope=lock_scope), timeout=lock_timeout
                    )
                    store.record_event(
                        "locks_acquired",
                        payload={"locks": [item.name for item in acquired_locks]},
                    )
                rc = self._execute_plan(
                    job=job,
                    plan=plan,
                    store=store,
                    run_id=run_id,
                    dry_run=dry_run,
                    variables=variables,
                    secrets=secrets,
                    from_node=from_node,
                    skip_successful=skip_successful,
                    only_failed=only_failed,
                    output_format=output_format,
                )
            finally:
                if lock_manager:
                    lock_manager.release_many(acquired_locks)
            store.update_run_status(self._final_run_status(store, rc))
            store.record_event("job_finished", payload={"rc": rc})
            self._print_run_summary(store, rc=rc, state_dir=state_dir, output_format=output_format)
            return rc
        except Exception as exc:
            store.update_run_status(NodeStatus.FAILED)
            store.record_event("job_failed", payload={"error": self._mask_text(str(exc), secrets)})
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
        skip_successful: bool = False,
        only_failed: bool = False,
        output_format: str = "text",
        lock: bool = False,
        lock_scope: str = "both",
        lock_timeout: float = 0,
    ) -> int:
        """Resume a previous run using paths stored in the run state."""
        self._validate_output_format(output_format)
        store = StateStore(state_dir, run_id)
        run = store.get_run()
        if not run:
            raise AutomaxError(f"run not found: {run_id}")
        if only_failed:
            failed = store.node_keys_by_status({NodeStatus.FAILED.value})
            if not failed:
                raise AutomaxError(f"run has no failed nodes: {run_id}")
        else:
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
            skip_successful=skip_successful,
            only_failed=only_failed,
            output_format=output_format,
            lock=lock,
            lock_scope=lock_scope,
            lock_timeout=lock_timeout,
        )

    def inspect_job(
        self,
        *,
        job_path: str,
        inventory_path: str,
        vars_path: str | None = None,
        secrets_path: str | None = None,
        limit: Iterable[str] = (),
        exclude: Iterable[str] = (),
        tags: Iterable[str] = (),
        skip_tags: Iterable[str] = (),
        cli_vars: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return a resolved, serializable view of a job without creating run state."""
        documents = self._load_documents(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
        )
        secrets = self.secret_manager.resolve_all(
            documents["secrets"],
            base_dir=Path(secrets_path).expanduser().resolve().parent if secrets_path else None,
        )
        variables = self._merge_variables(
            documents["vars"], documents["job"].get("vars", {}), cli_vars or {}
        )
        context = {"vars": variables, "secrets": secrets}
        inventory_document = load_inventory_document(inventory_path, context)
        inventory = Inventory(inventory_document, context)
        job = documents["job"]
        self.validate_job(job)
        plan = self._build_plan(
            job,
            inventory,
            limit=limit,
            exclude=exclude,
            tags=tags,
            skip_tags=skip_tags,
        )
        return build_job_view(job, plan)

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
        strict: bool = False,
    ) -> None:
        """Validate external YAML files without executing."""
        documents = self._load_documents(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
        )
        secrets = self.secret_manager.resolve_all(
            documents["secrets"],
            base_dir=Path(secrets_path).expanduser().resolve().parent if secrets_path else None,
        )
        variables = self._merge_variables(
            documents["vars"], documents["job"].get("vars", {}), cli_vars or {}
        )
        context = {"vars": variables, "secrets": secrets}
        inventory_document = load_inventory_document(inventory_path, context)
        inventory = Inventory(inventory_document, context)
        job = documents["job"]
        self.validate_job(job, strict=strict)
        plan = self._build_plan(job, inventory, limit=(), exclude=(), tags=tags, skip_tags=skip_tags)
        if strict:
            self._validate_plan_strict(plan)

    def validate_job(self, job: Dict[str, Any], *, strict: bool = False) -> None:
        """Validate the canonical three-level job DSL."""
        if job.get("apiVersion") != "automax.io/v1":
            raise AutomaxError("job apiVersion must be 'automax.io/v1'")
        if job.get("kind") != "Job":
            raise AutomaxError("job kind must be 'Job'")
        if strict:
            self._validate_known_keys(
                job,
                "job",
                {
                    "apiVersion",
                    "kind",
                    "metadata",
                    "vars",
                    "targets",
                    "strategy",
                    "failurePolicy",
                    "errorPolicy",
                    "timeouts",
                    "retry",
                    "tags",
                    "tasks",
                },
            )
        self._validate_strategy(job.get("strategy"), "job")
        self._validate_failure_policy(job.get("failurePolicy"), "job")
        self._validate_error_policy(job.get("errorPolicy"), "job")
        self._validate_timeouts(job.get("timeouts"), "job")
        self._validate_retry_policy(job.get("retry"), "job")
        tasks = job.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise AutomaxError("job requires non-empty tasks list")

        seen_tasks = set()
        for task in tasks:
            task_id = self._require_id(task, "task")
            if strict:
                self._validate_known_keys(
                    task,
                    f"task '{task_id}'",
                    {
                        "id",
                        "name",
                        "description",
                        "vars",
                        "targets",
                        "strategy",
                        "failurePolicy",
                        "errorPolicy",
                        "timeouts",
                        "retry",
                        "tags",
                        "steps",
                    },
                )
            self._validate_strategy(task.get("strategy"), f"task '{task_id}'")
            self._validate_failure_policy(task.get("failurePolicy"), f"task '{task_id}'")
            self._validate_error_policy(task.get("errorPolicy"), f"task '{task_id}'")
            self._validate_timeouts(task.get("timeouts"), f"task '{task_id}'")
            self._validate_retry_policy(task.get("retry"), f"task '{task_id}'")
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
                if strict:
                    self._validate_known_keys(
                        step,
                        f"step '{task_id}:{step_id}'",
                        {
                            "id",
                            "name",
                            "description",
                            "vars",
                            "targets",
                            "strategy",
                            "failurePolicy",
                            "errorPolicy",
                            "timeouts",
                            "retry",
                            "tags",
                            "substeps",
                        },
                    )
                self._validate_strategy(step.get("strategy"), f"step '{task_id}:{step_id}'")
                self._validate_failure_policy(step.get("failurePolicy"), f"step '{task_id}:{step_id}'")
                self._validate_error_policy(step.get("errorPolicy"), f"step '{task_id}:{step_id}'")
                self._validate_timeouts(step.get("timeouts"), f"step '{task_id}:{step_id}'")
                self._validate_retry_policy(step.get("retry"), f"step '{task_id}:{step_id}'")
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
                    if strict:
                        self._validate_known_keys(
                            substep,
                            f"substep '{task_id}:{step_id}:{substep_id}'",
                            {
                                "id",
                                "name",
                                "description",
                                "targets",
                                "tags",
                                "timeouts",
                                "retry",
                                "errorPolicy",
                                "when",
                                "use",
                                "plugin",
                                "with",
                                "params",
                                "register",
                                "artifacts",
                                "artifact",
                            },
                        )
                    self._validate_tags(
                        substep.get("tags"), f"substep '{task_id}:{step_id}:{substep_id}'"
                    )
                    self._validate_timeouts(
                        substep.get("timeouts"), f"substep '{task_id}:{step_id}:{substep_id}'"
                    )
                    self._validate_retry_policy(
                        substep.get("retry"), f"substep '{task_id}:{step_id}:{substep_id}'"
                    )
                    self._validate_error_policy(
                        substep.get("errorPolicy"), f"substep '{task_id}:{step_id}:{substep_id}'"
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

    def _validate_plan_strict(self, plan: List[Dict[str, Any]]) -> None:
        """Validate plugin parameters after target/tag resolution."""
        for item in plan:
            substep = item["substep"]
            plugin_name = str(substep.get("use") or substep.get("plugin"))
            plugin = self.plugin_registry.get(plugin_name)
            params = substep.get("with", substep.get("params", {})) or {}
            if not isinstance(params, dict):
                raise AutomaxError(f"substep '{item['node_id']}' params must be mapping")
            allowed = set(plugin.required_params) | set(plugin.optional_params)
            unknown = sorted(set(params) - allowed)
            if unknown:
                raise AutomaxError(
                    f"substep '{item['node_id']}' plugin '{plugin.name}' unknown params: "
                    + ", ".join(unknown)
                )

    @staticmethod
    def _validate_known_keys(node: Dict[str, Any], label: str, allowed: set[str]) -> None:
        unknown = sorted(set(node) - allowed)
        if unknown:
            raise AutomaxError(
                f"{label} has unsupported keys: {', '.join(unknown)}. "
                f"Allowed keys: {', '.join(sorted(allowed))}"
            )

    def _load_documents(self, **paths: str | None) -> Dict[str, Dict[str, Any]]:
        return {
            "job": load_yaml_file(paths["job_path"]),
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
        skip_successful: bool = False,
        only_failed: bool = False,
        output_format: str = "text",
    ) -> int:
        outputs: Dict[str, Any] = {}
        started = from_node is None
        failed_hosts: set[str] = set()
        stopped_tasks: set[str] = set()
        rc = 0
        previous_statuses = store.node_status_map() if (skip_successful or only_failed) else {}

        stages = self._group_by_stage(plan)
        for stage in stages:
            stage_groups: List[List[Dict[str, Any]]] = []
            for original_group in stage:
                group = self._filter_group_by_resume_status(
                    original_group,
                    previous_statuses=previous_statuses,
                    skip_successful=skip_successful,
                    only_failed=only_failed,
                )
                if not group:
                    continue
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
                output_format=output_format,
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

    @staticmethod
    def _filter_group_by_resume_status(
        group: List[Dict[str, Any]],
        *,
        previous_statuses: Dict[tuple[str, str], str],
        skip_successful: bool,
        only_failed: bool,
    ) -> List[Dict[str, Any]]:
        """Filter a step group for resume modes without rewriting existing rows."""
        if not previous_statuses or not (skip_successful or only_failed):
            return group
        filtered: List[Dict[str, Any]] = []
        for item in group:
            key = (item["node_id"], item["target"].name)
            status = previous_statuses.get(key)
            if only_failed:
                if status == NodeStatus.FAILED.value:
                    filtered.append(item)
                continue
            if skip_successful and status in {NodeStatus.SUCCESS.value, NodeStatus.WARNING.value}:
                continue
            filtered.append(item)
        return filtered

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
        output_format: str,
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
                    output_format=output_format,
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
                output_format=output_format,
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
                        output_format=output_format,
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
        output_format: str,
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
                        output_format=output_format,
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
        output_format: str,
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        first = group[0]
        task = first["task"]
        step = first["step"]
        target = self._target_with_step_timeouts(first["target"], job, task, step)
        group = [dict(item, target=target) for item in group]
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
                        output_format=output_format,
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
                    output_format=output_format,
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
                    message=self._mask_text(str(exc), secrets),
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
        output_format: str,
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
            result = self._execute_substep_with_retry(
                job=job,
                task=task,
                step=step,
                substep=substep,
                target=target,
                node_id=node_id,
                store=store,
                run_id=run_id,
                dry_run=dry_run,
                variables=variables,
                secrets=secrets,
                outputs=outputs,
                ssh_client=ssh_client,
                step_state=step_state,
                output_format=output_format,
            )

            with self._output_lock:
                self._register_outputs(outputs, node_id, target.name, substep, result)
            artifact_error = self._capture_declared_artifacts(
                store=store,
                job=job,
                item=item,
                result=result,
                variables=variables,
                secrets=secrets,
                outputs=outputs,
            )
            if artifact_error:
                result = PluginResult.failure(message=artifact_error)
            store.finish_node(
                node_id=node_id,
                target=target.name,
                status=self._node_status_for_result(result),
                changed=result.changed,
                rc=result.rc,
                message=self._mask_text(result.message, secrets),
                output=self._result_to_mapping(result, secrets=secrets),
            )
            store.record_event(
                "substep_finished",
                node_id=node_id,
                target=target.name,
                payload={"ok": result.ok, "changed": result.changed, "rc": result.rc},
            )
            if output_format == "text":
                status = "WARN" if result.warning else ("OK" if result.ok else "FAILED")
                with self._print_lock:
                    print(
                        f"[{status}] {target.name} {node_id} rc={result.rc} {self._mask_text(result.message, secrets)}".rstrip()
                    )
            if not result.ok:
                return 1
        return 0

    def _execute_substep_with_retry(
        self,
        *,
        job: Dict[str, Any],
        task: Dict[str, Any],
        step: Dict[str, Any],
        substep: Dict[str, Any],
        target: Target,
        node_id: str,
        store: StateStore,
        run_id: str,
        dry_run: bool,
        variables: Dict[str, Any],
        secrets: Dict[str, Any],
        outputs: Dict[str, Any],
        ssh_client: Any,
        step_state: Dict[str, Any],
        output_format: str,
    ) -> PluginResult:
        """Execute one substep with inherited retry policy and visible retry events."""
        policy = self._resolve_retry_policy(job, task, step, substep)
        attempts = int(policy["attempts"])
        attempt_records: list[Dict[str, Any]] = []
        result = PluginResult.failure(message="substep did not execute")
        for attempt in range(1, attempts + 1):
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
                result = self._apply_error_policy(job, task, step, substep, result, secrets)
            except Exception as exc:
                result = PluginResult.failure(message=str(exc))
            attempt_records.append(
                {
                    "attempt": attempt,
                    "ok": result.ok,
                    "rc": result.rc,
                    "message": self._mask_text(result.message, secrets),
                }
            )
            if result.ok or attempt >= attempts or not self._should_retry_result(result, policy):
                break
            delay = self._retry_delay(policy, attempt)
            retry_payload = {
                "attempt": attempt,
                "next_attempt": attempt + 1,
                "attempts": attempts,
                "rc": result.rc,
                "delay": delay,
                "message": self._mask_text(result.message, secrets),
            }
            store.record_event("substep_retry", node_id=node_id, target=target.name, payload=retry_payload)
            if output_format == "text":
                with self._print_lock:
                    print(
                        f"[RETRY] {target.name} {node_id} attempt={attempt}/{attempts} "
                        f"rc={result.rc} next={attempt + 1} delay={delay:g}s "
                        f"{self._mask_text(result.message, secrets)}".rstrip()
                    )
            if delay > 0:
                time.sleep(delay)
        if attempt_records:
            result.data = dict(result.data)
            result.data["attempts"] = attempt_records
            result.data["attempt"] = attempt_records[-1]["attempt"]
        return result

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
            command_timeout=self._resolve_command_timeout(job, task, step, substep),
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

    def _capture_declared_artifacts(
        self,
        *,
        store: StateStore,
        job: Dict[str, Any],
        item: Dict[str, Any],
        result: PluginResult,
        variables: Dict[str, Any],
        secrets: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> str | None:
        """Persist stdout/stderr/data artifacts declared by a substep."""
        substep = item["substep"]
        declaration = substep.get("artifacts", substep.get("artifact"))
        if not declaration:
            return None
        target = item["target"]
        source_values = {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "data": json.dumps(self._mask_mapping(result.data, secrets), indent=2, sort_keys=True),
        }
        if declaration is True:
            declaration = {"stdout": "stdout.txt", "stderr": "stderr.txt"}
        if not isinstance(declaration, dict):
            return "artifacts declaration must be a mapping or true"
        template_context = {
            "job": job,
            "task": item["task"],
            "step": item["step"],
            "substep": substep,
            "server": target,
            "target": target,
            "vars": variables,
            "outputs": outputs,
            "secrets": secrets,
            "run": {"id": store.run_id},
            "result": self._result_to_mapping(result, secrets=secrets),
        }
        try:
            for source, raw_name in declaration.items():
                source_name = str(source)
                if source_name not in source_values:
                    return f"unsupported artifact source: {source_name}"
                if raw_name in (False, None):
                    continue
                name = f"{source_name}.txt" if raw_name is True else str(raw_name)
                rendered_name = render_value(name, template_context)
                store.write_artifact(
                    node_id=item["node_id"],
                    target=target.name,
                    name=rendered_name,
                    kind=source_name,
                    content=self._mask_text(source_values[source_name], secrets),
                )
        except Exception as exc:
            return f"artifact capture failed: {self._mask_text(str(exc), secrets)}"
        return None

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

    def _result_to_mapping(
        self, result: PluginResult, *, secrets: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        return {
            "ok": result.ok,
            "changed": result.changed,
            "skipped": result.skipped,
            "warning": result.warning,
            "rc": result.rc,
            "stdout": self._mask_text(result.stdout, secrets or {}),
            "stderr": self._mask_text(result.stderr, secrets or {}),
            "message": self._mask_text(result.message, secrets or {}),
            "data": self._mask_mapping(result.data, secrets or {}),
        }

    def _mask_mapping(self, value: Any, secrets: Dict[str, Any]) -> Any:
        if isinstance(value, dict):
            return {key: self._mask_mapping(item, secrets) for key, item in value.items()}
        if isinstance(value, list):
            return [self._mask_mapping(item, secrets) for item in value]
        if isinstance(value, tuple):
            return tuple(self._mask_mapping(item, secrets) for item in value)
        if isinstance(value, str):
            return self._mask_text(value, secrets)
        return value

    @classmethod
    def _mask_text(cls, value: str, secrets: Dict[str, Any]) -> str:
        """Mask every printable secret value before logs/state/artifacts persist it."""
        masked = str(value)
        for secret_text in cls._iter_secret_texts(secrets):
            masked = masked.replace(secret_text, "***")
        return masked

    @classmethod
    def _iter_secret_texts(cls, value: Any) -> Iterable[str]:
        """Yield nested secret strings, ignoring tiny values that would over-mask logs."""
        if isinstance(value, dict):
            for item in value.values():
                yield from cls._iter_secret_texts(item)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                yield from cls._iter_secret_texts(item)
            return
        if value is None:
            return
        secret_text = str(value)
        if len(secret_text) >= 4:
            yield secret_text

    @staticmethod
    def _node_status_for_result(result: PluginResult) -> NodeStatus:
        if result.warning:
            return NodeStatus.WARNING
        return NodeStatus.SUCCESS if result.ok else NodeStatus.FAILED

    @staticmethod
    def _final_run_status(store: StateStore, rc: int) -> NodeStatus:
        if rc != 0:
            return NodeStatus.FAILED
        summary = store.summarize()
        if summary["status_counts"].get(NodeStatus.WARNING.value, 0):
            return NodeStatus.WARNING
        return NodeStatus.SUCCESS

    def _resolve_error_policy(
        self, job: Dict[str, Any], task: Dict[str, Any], step: Dict[str, Any], substep: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve inherited error normalization policy for one substep."""
        policy: Dict[str, Any] = {
            "acceptedRc": [],
            "expected": [],
            "fail": [],
            "unmatched": "fail",
            "acceptedStatus": "warning",
        }
        for node in (job, task, step, substep):
            raw = node.get("errorPolicy") or {}
            if raw:
                policy.update(raw)
        self._validate_error_policy(policy, "resolved errorPolicy")
        policy["acceptedRc"] = [int(value) for value in policy.get("acceptedRc", [])]
        policy["expected"] = self._normalize_error_rules(policy.get("expected", []), "expected")
        policy["fail"] = self._normalize_error_rules(policy.get("fail", []), "fail")
        return policy

    def _apply_error_policy(
        self,
        job: Dict[str, Any],
        task: Dict[str, Any],
        step: Dict[str, Any],
        substep: Dict[str, Any],
        result: PluginResult,
        secrets: Dict[str, Any],
    ) -> PluginResult:
        """Normalize accepted non-zero return codes into warning/success when safe."""
        if result.ok:
            return result
        policy = self._resolve_error_policy(job, task, step, substep)
        accepted_rc = set(policy.get("acceptedRc") or [])
        if int(result.rc) not in accepted_rc:
            return result

        fail_matches = self._match_error_rules(result, policy.get("fail", []))
        expected_matches = self._match_error_rules(result, policy.get("expected", []))
        unmatched_lines = self._unmatched_error_lines(result, expected_matches)
        unmatched_mode = str(policy.get("unmatched", "fail"))
        if fail_matches:
            result.data = dict(result.data)
            result.data["errorPolicy"] = self._error_policy_data(
                accepted=False,
                reason="fail pattern matched",
                expected_matches=expected_matches,
                fail_matches=fail_matches,
                unmatched_lines=unmatched_lines,
                policy=policy,
                secrets=secrets,
            )
            return result
        if unmatched_lines and unmatched_mode == "fail":
            result.data = dict(result.data)
            result.data["errorPolicy"] = self._error_policy_data(
                accepted=False,
                reason="unexpected output remained after expected diagnostics were removed",
                expected_matches=expected_matches,
                fail_matches=fail_matches,
                unmatched_lines=unmatched_lines,
                policy=policy,
                secrets=secrets,
            )
            return result

        status = str(policy.get("acceptedStatus", "warning"))
        message = self._accepted_error_policy_message(
            expected_matches=expected_matches,
            unmatched_lines=unmatched_lines,
            unmatched_mode=unmatched_mode,
        )
        data = dict(result.data)
        data["errorPolicy"] = self._error_policy_data(
            accepted=True,
            reason="accepted return code normalized by errorPolicy",
            expected_matches=expected_matches,
            fail_matches=fail_matches,
            unmatched_lines=unmatched_lines,
            policy=policy,
            secrets=secrets,
        )
        if status == "success" and unmatched_mode != "warn":
            return PluginResult.success(
                changed=result.changed,
                rc=result.rc,
                stdout=result.stdout,
                stderr=result.stderr,
                message=message,
                data=data,
            )
        return PluginResult.warning_result(
            changed=result.changed,
            rc=result.rc,
            stdout=result.stdout,
            stderr=result.stderr,
            message=message,
            data=data,
        )

    @staticmethod
    def _accepted_error_policy_message(
        *, expected_matches: list[Dict[str, Any]], unmatched_lines: list[Dict[str, Any]], unmatched_mode: str
    ) -> str:
        suffix = ""
        if unmatched_lines and unmatched_mode == "warn":
            suffix = f", {len(unmatched_lines)} unexpected line(s) downgraded to warning"
        return (
            "accepted failure by errorPolicy: "
            f"{len(expected_matches)} expected diagnostic(s), "
            f"{len(unmatched_lines)} unexpected diagnostic(s){suffix}"
        )

    def _error_policy_data(
        self,
        *,
        accepted: bool,
        reason: str,
        expected_matches: list[Dict[str, Any]],
        fail_matches: list[Dict[str, Any]],
        unmatched_lines: list[Dict[str, Any]],
        policy: Dict[str, Any],
        secrets: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self._mask_mapping(
            {
                "accepted": accepted,
                "reason": reason,
                "acceptedRc": policy.get("acceptedRc", []),
                "acceptedStatus": policy.get("acceptedStatus", "warning"),
                "unmatched": policy.get("unmatched", "fail"),
                "expectedMatches": expected_matches,
                "failMatches": fail_matches,
                "unexpectedLines": unmatched_lines[:50],
                "unexpectedLineCount": len(unmatched_lines),
            },
            secrets,
        )

    def _match_error_rules(
        self, result: PluginResult, rules: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        matches: list[Dict[str, Any]] = []
        stream_lines = self._error_policy_stream_lines(result)
        for rule in rules:
            pattern = re.compile(str(rule["pattern"]))
            stream = str(rule.get("stream", "combined"))
            for line in stream_lines[stream]:
                if pattern.search(line["text"]):
                    matches.append(
                        {
                            "stream": line["source"],
                            "line": line["text"],
                            "pattern": str(rule["pattern"]),
                            "reason": str(rule.get("reason", "")),
                        }
                    )
        return matches

    def _unmatched_error_lines(
        self, result: PluginResult, expected_matches: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        matched = {(item["stream"], item["line"]) for item in expected_matches}
        lines = self._error_policy_stream_lines(result)["combined"]
        return [
            {"stream": line["source"], "line": line["text"]}
            for line in lines
            if (line["source"], line["text"]) not in matched
        ]

    @staticmethod
    def _error_policy_stream_lines(result: PluginResult) -> Dict[str, list[Dict[str, str]]]:
        stdout = [
            {"source": "stdout", "text": line}
            for line in str(result.stdout or "").splitlines()
            if line.strip()
        ]
        stderr = [
            {"source": "stderr", "text": line}
            for line in str(result.stderr or "").splitlines()
            if line.strip()
        ]
        message = [
            {"source": "message", "text": line}
            for line in str(result.message or "").splitlines()
            if line.strip()
        ]
        return {
            "stdout": stdout,
            "stderr": stderr,
            "message": message,
            "combined": [*stdout, *stderr],
        }

    @staticmethod
    def _normalize_error_rules(value: Any, label: str) -> list[Dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, (str, dict)):
            value = [value]
        if not isinstance(value, list):
            raise AutomaxError(f"{label} errorPolicy rules must be a list")
        rules: list[Dict[str, Any]] = []
        for item in value:
            if isinstance(item, str):
                rules.append({"stream": "combined", "pattern": item})
                continue
            if not isinstance(item, dict):
                raise AutomaxError(f"{label} errorPolicy rule must be a mapping or string")
            if not item.get("pattern"):
                raise AutomaxError(f"{label} errorPolicy rule requires pattern")
            stream = str(item.get("stream", "combined"))
            if stream not in {"stdout", "stderr", "combined", "message"}:
                raise AutomaxError(
                    f"{label} errorPolicy rule stream must be stdout, stderr, combined or message"
                )
            re.compile(str(item["pattern"]))
            rules.append(
                {
                    "stream": stream,
                    "pattern": str(item["pattern"]),
                    "reason": str(item.get("reason", "")),
                }
            )
        return rules

    @classmethod
    def _validate_error_policy(cls, policy: Any, label: str) -> None:
        if policy is None:
            return
        if not isinstance(policy, dict):
            raise AutomaxError(f"{label} errorPolicy must be a mapping")
        allowed = {"acceptedRc", "expected", "fail", "unmatched", "acceptedStatus"}
        unknown = sorted(set(policy) - allowed)
        if unknown:
            raise AutomaxError(
                f"{label} errorPolicy unsupported keys: {', '.join(unknown)}. "
                f"Allowed keys: {', '.join(sorted(allowed))}"
            )
        accepted_rc = policy.get("acceptedRc", [])
        if accepted_rc is None:
            accepted_rc = []
        if isinstance(accepted_rc, int):
            raise AutomaxError(f"{label} errorPolicy acceptedRc must be a list of integers")
        if not isinstance(accepted_rc, list):
            raise AutomaxError(f"{label} errorPolicy acceptedRc must be a list of integers")
        for value in accepted_rc:
            int(value)
        unmatched = str(policy.get("unmatched", "fail"))
        if unmatched not in {"fail", "warn", "ignore"}:
            raise AutomaxError(f"{label} errorPolicy unmatched must be fail, warn or ignore")
        accepted_status = str(policy.get("acceptedStatus", "warning"))
        if accepted_status not in {"warning", "success"}:
            raise AutomaxError(f"{label} errorPolicy acceptedStatus must be warning or success")
        cls._normalize_error_rules(policy.get("expected", []), f"{label} expected")
        cls._normalize_error_rules(policy.get("fail", []), f"{label} fail")

    def _resolve_retry_policy(
        self, job: Dict[str, Any], task: Dict[str, Any], step: Dict[str, Any], substep: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve inherited retry policy for one substep."""
        policy: Dict[str, Any] = {"attempts": 1, "delay": 0.0, "backoff": "fixed"}
        for node in (job, task, step, substep):
            raw = node.get("retry") or {}
            if raw:
                policy.update(raw)
        self._validate_retry_policy(policy, "resolved retry")
        policy["attempts"] = int(policy.get("attempts", 1) or 1)
        policy["delay"] = float(policy.get("delay", 0) or 0)
        if "max_delay" in policy:
            policy["max_delay"] = float(policy["max_delay"])
        if "maxDelay" in policy:
            policy["maxDelay"] = float(policy["maxDelay"])
        return policy

    @staticmethod
    def _should_retry_result(result: PluginResult, policy: Dict[str, Any]) -> bool:
        """Return whether a failed result is eligible for another attempt."""
        if result.ok:
            return False
        retry_on_rc = policy.get("retry_on_rc", policy.get("retryOnRc"))
        if retry_on_rc is None:
            return True
        if isinstance(retry_on_rc, int):
            allowed = {retry_on_rc}
        else:
            allowed = {int(value) for value in retry_on_rc}
        return int(result.rc) in allowed

    @staticmethod
    def _retry_delay(policy: Dict[str, Any], attempt: int) -> float:
        """Return delay before the next retry attempt."""
        base = float(policy.get("delay", 0) or 0)
        backoff = str(policy.get("backoff", "fixed"))
        if backoff == "exponential" and base > 0:
            delay = base * (2 ** max(0, attempt - 1))
        else:
            delay = base
        max_delay = policy.get("max_delay", policy.get("maxDelay"))
        if max_delay is not None:
            delay = min(delay, float(max_delay))
        return delay

    @staticmethod
    def _validate_retry_policy(retry: Any, label: str) -> None:
        """Validate inherited retry policy mappings."""
        if retry is None:
            return
        if not isinstance(retry, dict):
            raise AutomaxError(f"{label} retry must be a mapping")
        allowed = {"attempts", "delay", "backoff", "max_delay", "maxDelay", "retry_on_rc", "retryOnRc"}
        unknown = sorted(set(retry) - allowed)
        if unknown:
            raise AutomaxError(
                f"{label} retry unsupported keys: {', '.join(unknown)}. "
                f"Allowed keys: {', '.join(sorted(allowed))}"
            )
        if int(retry.get("attempts", 1) or 1) < 1:
            raise AutomaxError(f"{label} retry attempts must be >= 1")
        if float(retry.get("delay", 0) or 0) < 0:
            raise AutomaxError(f"{label} retry delay must be >= 0")
        backoff = str(retry.get("backoff", "fixed"))
        if backoff not in {"fixed", "exponential"}:
            raise AutomaxError(f"{label} retry backoff must be fixed or exponential")
        max_delay = retry.get("max_delay", retry.get("maxDelay"))
        if max_delay is not None and float(max_delay) < 0:
            raise AutomaxError(f"{label} retry max_delay must be >= 0")
        retry_on_rc = retry.get("retry_on_rc", retry.get("retryOnRc"))
        if retry_on_rc is not None:
            values = [retry_on_rc] if isinstance(retry_on_rc, int) else retry_on_rc
            if not isinstance(values, list) or not values:
                raise AutomaxError(f"{label} retry retry_on_rc must be a non-empty list of integers")
            for value in values:
                int(value)

    def _target_with_step_timeouts(
        self, target: Target, job: Dict[str, Any], task: Dict[str, Any], step: Dict[str, Any]
    ) -> Target:
        """Merge job/task/step SSH timeout controls into the target."""
        timeouts = self._merged_timeouts(job, task, step)
        if not timeouts:
            return target
        ssh = dict(target.ssh)
        mapping = {
            "ssh_connect": "connect_timeout",
            "connect": "connect_timeout",
            "ssh_banner": "banner_timeout",
            "banner": "banner_timeout",
            "ssh_auth": "auth_timeout",
            "auth": "auth_timeout",
        }
        for source, dest in mapping.items():
            if source in timeouts:
                ssh[dest] = int(timeouts[source])
        return replace(target, ssh=ssh)

    def _resolve_command_timeout(
        self, job: Dict[str, Any], task: Dict[str, Any], step: Dict[str, Any], substep: Dict[str, Any]
    ) -> int | None:
        """Resolve the inherited default command timeout for a substep."""
        timeouts = self._merged_timeouts(job, task, step, substep)
        value = timeouts.get("command") or timeouts.get("command_timeout")
        return int(value) if value is not None else None

    @staticmethod
    def _merged_timeouts(*nodes: Dict[str, Any]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for node in nodes:
            raw = node.get("timeouts") or {}
            if raw:
                merged.update(raw)
        return merged

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

    @classmethod
    def _lock_names(cls, job: Dict[str, Any], plan: List[Dict[str, Any]], *, scope: str) -> list[str]:
        """Return lock names for a planned run."""
        if scope not in {"job", "target", "both"}:
            raise AutomaxError("lock scope must be one of: job, target, both")
        job_name = cls._job_name(job)
        names: list[str] = []
        if scope in {"job", "both"}:
            names.append(f"job:{job_name}")
        if scope in {"target", "both"}:
            for target_name in sorted({item["target"].name for item in plan}):
                names.append(f"target:{target_name}")
        return names

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
    def _validate_output_format(output_format: str) -> None:
        if output_format not in {"text", "json"}:
            raise AutomaxError(f"unsupported output format: {output_format}")

    @staticmethod
    def _run_summary_payload(store: StateStore, *, rc: int, state_dir: str) -> Dict[str, Any]:
        summary = store.summarize()
        first_failed = summary["failed_nodes"][0]["node_id"] if summary["failed_nodes"] else None
        resume: Dict[str, str] = {
            "default": f"automax resume {store.run_id} --state-dir {state_dir}",
        }
        if first_failed:
            resume.update(
                {
                    "skip_successful": f"automax resume {store.run_id} --state-dir {state_dir} --skip-successful",
                    "only_failed": f"automax resume {store.run_id} --state-dir {state_dir} --only-failed",
                    "from": f"automax resume {store.run_id} --state-dir {state_dir} --from {first_failed}",
                }
            )
        return {
            "run_id": store.run_id,
            "rc": rc,
            "status": summary["run"]["status"],
            "run": summary["run"],
            "state_dir": str(store.run_dir),
            "summary": {
                "targets": summary["targets_total"],
                "nodes": summary["nodes_total"],
                "success": summary["status_counts"].get(NodeStatus.SUCCESS.value, 0),
                "warning": summary["status_counts"].get(NodeStatus.WARNING.value, 0),
                "failed": summary["status_counts"].get(NodeStatus.FAILED.value, 0),
                "skipped": summary["status_counts"].get(NodeStatus.SKIPPED.value, 0),
                "changed": summary["changed_nodes"],
                "artifacts": summary["artifacts_count"],
            },
            "targets": summary["targets"],
            "failed_nodes": summary["failed_nodes"],
            "warning_nodes": summary.get("warning_nodes", []),
            "first_failed_node": summary["first_failed_node"],
            "resume": resume,
            "artifacts_command": f"automax artifacts list {store.run_id} --state-dir {state_dir}"
            if summary["artifacts_count"]
            else None,
        }

    @classmethod
    def _print_run_summary(
        cls,
        store: StateStore,
        *,
        rc: int,
        state_dir: str,
        output_format: str = "text",
    ) -> None:
        """Print a compact operator summary after each real run/resume."""
        payload = cls._run_summary_payload(store, rc=rc, state_dir=state_dir)
        if output_format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
            return

        run = payload["run"]
        failed_nodes = payload["failed_nodes"]
        warning_nodes = payload.get("warning_nodes", [])
        status_word = "succeeded" if rc == 0 else "failed"
        print("")
        print(f"Automax run {status_word}")
        print(f"Run ID: {store.run_id}")
        print(f"Status: {run['status']}")
        print(f"Job: {run['job_path']}")
        print(f"State: {payload['state_dir']}")
        print("Summary:")
        for key in ("targets", "nodes", "success", "warning", "failed", "skipped", "changed", "artifacts"):
            print(f"  {key}: {payload['summary'][key]}")
        if payload["targets"]:
            print("Targets:")
            for target in payload["targets"]:
                counts = target["status_counts"]
                print(
                    "  "
                    f"{target['target']} {target['status']} "
                    f"changed={target['changed']} "
                    f"success={counts.get(NodeStatus.SUCCESS.value, 0)} "
                    f"warning={counts.get(NodeStatus.WARNING.value, 0)} "
                    f"failed={counts.get(NodeStatus.FAILED.value, 0)} "
                    f"skipped={counts.get(NodeStatus.SKIPPED.value, 0)}"
                )
        if warning_nodes:
            print("Warnings:")
            for node in warning_nodes[:10]:
                detail = f" rc={node['rc']}" if node.get("rc") is not None else ""
                message = f" {node['message']}" if node.get("message") else ""
                print(f"  {node['target']} {node['node_id']}{detail}{message}".rstrip())
            if len(warning_nodes) > 10:
                print(f"  ... {len(warning_nodes) - 10} more warning nodes")
        if failed_nodes:
            print("Failed:")
            for node in failed_nodes[:10]:
                detail = f" rc={node['rc']}" if node.get("rc") is not None else ""
                message = f" {node['message']}" if node.get("message") else ""
                print(f"  {node['target']} {node['node_id']}{detail}{message}".rstrip())
            if len(failed_nodes) > 10:
                print(f"  ... {len(failed_nodes) - 10} more failed nodes")
            print("Resume options:")
            for key in ("skip_successful", "only_failed", "from"):
                if key in payload["resume"]:
                    print(f"  {payload['resume'][key]}")
        if payload["artifacts_command"]:
            print("Artifacts:")
            print(f"  {payload['artifacts_command']}")

    @staticmethod
    def _plan_payload(run_id: str, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "run_id": run_id,
            "nodes": [
                {
                    "target": item["target"].name,
                    "node_id": item["node_id"],
                    "task_id": item["task"]["id"],
                    "step_id": item["step"]["id"],
                    "substep_id": item["substep"]["id"],
                    "plugin": str(item["substep"].get("use") or item["substep"].get("plugin")),
                    "tags": list(item.get("tags") or ()),
                }
                for item in plan
            ],
        }

    @classmethod
    def _print_plan(
        cls, run_id: str, plan: List[Dict[str, Any]], *, output_format: str = "text"
    ) -> None:
        payload = cls._plan_payload(run_id, plan)
        if output_format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
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

    @staticmethod
    def _validate_timeouts(timeouts: Any, label: str) -> None:
        """Validate inherited timeout mappings."""
        if timeouts is None:
            return
        if not isinstance(timeouts, dict):
            raise AutomaxError(f"{label} timeouts must be a mapping")
        allowed = {
            "command",
            "command_timeout",
            "ssh_connect",
            "connect",
            "ssh_banner",
            "banner",
            "ssh_auth",
            "auth",
        }
        for key, value in timeouts.items():
            if key not in allowed:
                raise AutomaxError(
                    f"{label} timeouts unsupported key '{key}'. Allowed: {', '.join(sorted(allowed))}"
                )
            if int(value) <= 0:
                raise AutomaxError(f"{label} timeout {key} must be a positive integer")

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
