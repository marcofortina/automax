# Send Email Plugin

Send emails via SMTP.

## Configuration

**Required:**
- `smtp_server`: SMTP server hostname
- `port`: SMTP server port
- `username`: SMTP username
- `password`: SMTP password
- `to`: Recipient email address(es)
- `subject`: Email subject
- `body`: Email body

**Optional:**
- `from_addr`: Sender address (default: username)
- `cc`: CC recipients
- `bcc`: BCC recipients
- `is_html`: Body is HTML (default: false)

## Example

```yaml
plugin: send_email
config:
  smtp_server: "smtp.gmail.com"
  port: 587
  username: "user@gmail.com"
  password: "app-password"
  to: "recipient@example.com"
  subject: "Test Email"
  body: "This is a test email"
  is_html: false
```

## Return Values

The plugin returns a dictionary with:
- `status`: "success" or "failure"
- `smtp_server`: The SMTP server
- `port`: The SMTP port
- `from`: The sender address
- `to`: The recipient address(es)
- `subject`: The email subject
