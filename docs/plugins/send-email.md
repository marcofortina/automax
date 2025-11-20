# Send Email Plugin

Send emails via SMTP protocol.

## Description

This plugin enables sending emails through SMTP servers. It supports HTML and plain text content, file attachments, multiple recipients, and various authentication methods.

## Configuration

### Required Parameters

- `smtp_server` (string): SMTP server hostname
- `smtp_port` (integer): SMTP server port
- `from_address` (string): Sender email address
- `to_addresses` (array): List of recipient email addresses
- `subject` (string): Email subject line

### Optional Parameters

- `username` (string): SMTP authentication username
- `password` (string): SMTP authentication password
- `body` (string): Email body content
- `body_html` (string): HTML email body content
- `cc_addresses` (array): List of CC recipient email addresses
- `bcc_addresses` (array): List of BCC recipient email addresses
- `attachments` (array): List of file paths to attach
- `use_tls` (boolean): Use TLS encryption (default: true)
- `use_ssl` (boolean): Use SSL encryption (default: false)
- `timeout` (integer): Connection timeout in seconds (default: 30)

## Examples

### Send Simple Text Email

```yaml
- name: send_notification
  plugin: send_email
  parameters:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    from_address: "noreply@example.com"
    to_addresses:
      - "user@example.com"
    subject: "Automax Notification"
    body: "This is a test email from Automax."
    username: "your-email@gmail.com"
    password: "your-app-password"
    use_tls: true
```

### Send HTML Email with CC

```yaml
- name: send_html_newsletter
  plugin: send_email
  parameters:
    smtp_server: "smtp.company.com"
    smtp_port: 465
    from_address: "newsletter@company.com"
    to_addresses:
      - "subscriber1@example.com"
      - "subscriber2@example.com"
    cc_addresses:
      - "manager@company.com"
    subject: "Monthly Newsletter"
    body: "This is the plain text version."
    body_html: "<h1>Monthly Newsletter</h1><p>This is the <strong>HTML</strong> version.</p>"
    username: "newsletter@company.com"
    password: "smtp-password"
    use_ssl: true
```

### Send Email with Attachments

```yaml
- name: send_report_with_attachments
  plugin: send_email
  parameters:
    smtp_server: "smtp.office365.com"
    smtp_port: 587
    from_address: "reports@company.com"
    to_addresses:
      - "team@company.com"
    subject: "Daily Report"
    body: "Please find the attached daily report."
    attachments:
      - "/reports/daily_report.pdf"
      - "/reports/data.csv"
    username: "reports@company.com"
    password: "email-password"
    use_tls: true
    timeout: 60
```

### Send Email without Authentication (Local SMTP)

```yaml
- name: send_local_notification
  plugin: send_email
  parameters:
    smtp_server: "localhost"
    smtp_port: 25
    from_address: "automax@localhost"
    to_addresses:
      - "admin@company.com"
    subject: "System Alert"
    body: "System check completed successfully."
    use_tls: false
```

## Return Values

### Success Response

```json
{
  "status": "success",
  "from_address": "noreply@example.com",
  "to_addresses": ["user@example.com"],
  "subject": "Automax Notification",
  "message_id": "<20230101120000.12345@example.com>",
  "sent_time": "2023-01-01T12:00:00Z"
}
```

### Error Response

```json
{
  "status": "error",
  "from_address": "noreply@example.com",
  "to_addresses": ["user@example.com"],
  "subject": "Automax Notification",
  "error": "SMTPAuthenticationError: Authentication failed",
  "details": "Username and Password not accepted."
}
```

## Troubleshooting

### Common Errors

- **`SMTPAuthenticationError`**: Authentication failed
  - Verify username and password are correct
  - Check if you're using app passwords for services like Gmail
  - Ensure the account is not locked or requires 2-factor authentication

- **`SMTPConnectError`**: Unable to connect to SMTP server
  - Verify SMTP server hostname and port
  - Check network connectivity and firewall rules
  - Ensure the SMTP server is running

- **`SMTPServerDisconnected`**: Connection unexpectedly closed
  - Check if the server has idle timeouts
  - Verify TLS/SSL configuration matches server requirements
  - Ensure credentials are correct

- **`Timeout`**: Connection or operation timed out
  - Increase timeout value for slow connections
  - Check network latency to SMTP server
  - Verify server performance

- **`FileNotFoundError`**: Attachment file not found
  - Verify attachment file paths are correct
  - Check file permissions and accessibility
  - Ensure files exist before sending

- **`SMTPRecipientsRefused`**: Recipient addresses rejected
  - Verify recipient email addresses are valid
  - Check if the domain exists
  - Ensure the sender is authorized to send to recipients

### Common SMTP Server Configurations

- **Gmail**: smtp.gmail.com, port 587 (TLS) or 465 (SSL)
- **Outlook/Office365**: smtp.office365.com, port 587 (TLS)
- **Yahoo**: smtp.mail.yahoo.com, port 587 (TLS) or 465 (SSL)
- **iCloud**: smtp.mail.me.com, port 587 (TLS)
- **SendGrid**: smtp.sendgrid.net, port 587 (TLS) or 465 (SSL)
- **Amazon SES**: email-smtp.us-east-1.amazonaws.com, port 587 (TLS)

### Best Practices

1. Use environment variables or secret managers for SMTP credentials
2. Implement proper error handling and retry mechanisms
3. Validate email addresses before sending
4. Use meaningful subject lines that reflect email content
5. Include both plain text and HTML versions for better compatibility
6. Compress large attachments before sending
7. Monitor email delivery rates and bouncebacks
8. Respect anti-spam regulations and recipient preferences

### Security Considerations

- Never hardcode email passwords in configuration files
- Use app-specific passwords for third-party email services
- Implement rate limiting to prevent abuse
- Validate and sanitize all email content to prevent injection attacks
- Use TLS encryption for sensitive information
- Regularly audit email sending patterns and permissions
