from fastmcp import FastMCP
import imaplib
import email
from typing import List, Annotated, Literal
from pydantic import Field
import os

USER = os.getenv("IMAP_USER")
PASSWORD = os.getenv("IMAP_PASSWORD")
SERVER = os.getenv("IMAP_SERVER")
if not USER:
    raise ValueError("IMAP_USER is not set or is empty")
if not PASSWORD:
    raise ValueError("IMAP_PASSWORD is not set or is empty")
if not SERVER:
    raise ValueError("IMAP_SERVER is not set or is empty")

mcp = FastMCP("IMAP Email Search Tool")

def extract_body(email_message):
    """Helper function to extract the body of an email message."""
    body = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            try:
                body = part.get_payload(decode=True).decode()
                if body != "":
                    break
            except:
                pass
    else:
        content_type = email_message.get_content_type()
        body = email_message.get_payload(decode=True).decode()
    return body, content_type


@mcp.tool
def view_email(
    email_id: Annotated[str, Field(description="ID of the email to retrieve")],
    mailbox: Annotated[str, Field(description="IMAP mailbox to check", default="INBOX")] = "INBOX"
) -> dict:
    """
    Retrieve details of a specific email.

    Args:
        email_id: ID of the email to retrieve.
        mailbox: IMAP mailbox to check (default: "INBOX").

    Returns:
        A dictionary with the email's subject, sender, and body.
    """
    try:
        mail = imaplib.IMAP4_SSL(SERVER)
        mail.login(USER, PASSWORD)
        mail.select(mailbox)
        status, data = mail.fetch(email_id, "(RFC822)")
        if status == "OK":
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            body, type = extract_body(email_message)
            return {
                "subject": email_message["Subject"],
                "from": email_message["From"],
                "body": body,
                "type": type,
            }
        else:
            raise Exception(f"Email {email_id} not found")
    except Exception as e:
        mail.logout()
        raise e


@mcp.tool
def delete_email(
    email_id: Annotated[str, Field(description="ID of the email to delete")],
    mailbox: Annotated[str, Field(description="IMAP mailbox to check", default="INBOX")] = "INBOX"
) -> dict:
    """
    Delete a specific email.

    Args:
        email_id: ID of the email to delete.
        mailbox: IMAP mailbox to check (default: "INBOX").

    Returns:
        A dictionary with the result of the deletion.
    """
    try:
        mail = imaplib.IMAP4_SSL(SERVER)
        mail.login(USER, PASSWORD)
        mail.select(mailbox)
        mail.store(email_id, "+FLAGS", "(DELETED)")
        mail.expunge()
        mail.logout()
        return {"status": "success", "email_id": email_id, "mailbox": mailbox}
    except Exception as e:
        mail.logout()
        raise e


@mcp.tool
def move_email(
    email_id: Annotated[str, Field(description="ID of the email to move")],
    target_mailbox: Annotated[str, Field(description="Target IMAP mailbox to move the email to")]
) -> dict:
    """
    Move an email to a different IMAP mailbox.

    Args:
        email_id: ID of the email to move.
        target_mailbox: Target IMAP mailbox to move the email to.

    Returns:
        A dictionary with the result of the move.
    """
    try:
        mail = imaplib.IMAP4_SSL(SERVER)
        mail.login(USER, PASSWORD)
        mail.select("INBOX")
        mail.copy(email_id, target_mailbox)
        mail.store(email_id, "+FLAGS", "(DELETED)")
        mail.expunge()
        mail.logout()
        return {"status": "success", "email_id": email_id, "target_mailbox": target_mailbox}
    except Exception as e:
        mail.logout()
        raise e


@mcp.tool
def list_mailboxes(
) -> list:
    """
    List all available IMAP mailboxes.

    Returns:
        A list of mailbox names.
    """
    try:
        mail = imaplib.IMAP4_SSL(SERVER)
        mail.login(USER, PASSWORD)
        status, data = mail.list()
        mailboxes = [item.decode().split('"."')[1].replace(" ","") for item in data]
        mail.logout()
        return mailboxes
    except Exception as e:
        mail.logout()
        raise e


@mcp.tool
def check_unseen(
) -> dict:
    """
    Check the number of unseen emails in the mailbox.

    Returns:
        A dict of email (with IDs as keys) that match the query.
    """
    try:
        mail = imaplib.IMAP4_SSL(SERVER)
        mail.login(USER, PASSWORD)
        mail.select("INBOX")
        status, recent = mail.search(None, "UNSEEN")
        email_ids = recent[0].split()
        result_subjects = {}

        for email_id in email_ids:
            status, data = mail.fetch(email_id, "(RFC822)")
            if status == "OK":
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                result_subjects[email_id] = {'Subject': email_message["Subject"], 'Date': email_message['Date']}
        
        mail.logout()
        return result_subjects
    except Exception as e:
        mail.logout()
        raise e

@mcp.tool
def search_emails(
    criterion: Annotated[Literal["ALL", "ANSWERED", "BCC", "BEFORE", "BODY", "CC", "DELETED", "DRAFT", "FLAGGED", "FROM", "HEADER", "KEYWORD", "LARGER", "NEW", "NOT", "OLD", "ON", "OR", "RECENT", "SEEN", "SENTBEFORE", "SENTON", "SENDSINCE", "SINCE", "SMALLER", "SUBJECT", "TEXT", "TO", "UID", "UNANSWERED", "UNDELETED", "UNDRAFT", "UNFLAGGED", "UNKEYWORD", "UNSEEN"], Field(description="Search criterion for emails. NOT, AND, OR are used to combine criterions.")],
    value: Annotated[str, Field(description='Value to match against the criterion. If a date based criterion is used (such as BEFORE, SINCE ...) the date format to use is something like "01-Jan-2012"')],
    mailbox: Annotated[str, Field(description="IMAP mailbox to search", default="INBOX")] = "INBOX"
) -> dict:
    """
    Search for emails based on a criterion and value.

    Args:
        criterion: Search criterion (e.g., "SUBJECT", "FROM", "BODY", etc.).
        value: Value to match against the criterion.
        mailbox: IMAP mailbox to search (default: "INBOX").

    Returns:
        A dict of email (with IDs as keys) that match the query.
    """
    try:
        mail = imaplib.IMAP4_SSL(SERVER)
        mail.login(USER, PASSWORD)
        mail.select(mailbox)

        status, messages = mail.search(None, criterion, value)
        if status != "OK":
            return ["No matching emails found."]

        email_ids = messages[0].split()
        result_subjects = {}

        for email_id in email_ids:
            status, data = mail.fetch(email_id, "(RFC822)")
            if status == "OK":
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                result_subjects[email_id] = {'Subject': email_message["Subject"], 'Date': email_message['Date']}

        mail.logout()
        return result_subjects
    except Exception as e:
        mail.logout()
        raise e

if __name__ == "__main__":
    mcp.run()