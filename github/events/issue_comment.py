import html
import re

from data_types.issue import Issue
from data_types.issue_comment import IssueComment
from data_types.repository import Repository
from data_types.user import User
from .base import EventBase


class EventIssueComment(EventBase):

    def __init__(self, sdk):
        super(EventIssueComment, self).__init__(sdk)
        self.issue = None
        self.repository = None
        self.sender = None
        self.sdk = sdk

    """
    IssueCommentEvent

    Triggered when an issue comment is created, edited, or deleted.

    https://developer.github.com/v3/activity/events/types/#issuecommentevent
    """

    async def process(self, payload, chat):
        """
        Processes IssueComment event
        :param payload: JSON object with payload
        :param chat: current chat object
        :return:
        """

        self.sdk.log("IssueComment event payload taken")

        try:
            self.issue = Issue(payload['issue'])
            self.comment = IssueComment(payload['comment'])
            self.repository = Repository(payload['repository'])
            self.sender = User(payload['sender'])

        except Exception as e:
            self.sdk.log('Cannot process IssueCommentEvent payload because of {}'.format(e))

        action = payload['action']

        available_actions = {
            'created': self.created
        }

        if action not in available_actions:
            self.sdk.log('Unsupported IssueComment action: {}'.format(action))
            return

        # call action handler
        await available_actions[action](chat['chat'], payload)

    async def created(self, chat_id, payload):
        """
        IssueComment created action
        :param chat_id: Current user chat token
        :param payload: GitHub payload
        :return:
        """

        issue_type = 'Issue'
        if self.issue.pull_request_url:
            issue_type = 'Pull request'

        message = "💬 <code>{} «{}»</code> [<a href=\"{}\">{}</a>]".format(
                        issue_type,
                        html.escape(self.issue.title),
                        self.repository.html_url,
                        self.repository.name
                    ) + "\n\n"

        if len(self.comment.body):
            # Remove blank and citation lines (starting with "> ")
            # Truncate text to maximum 10 lines and 250 symbols
            full_body = html.escape(self.comment.body)
            author_body = "\n".join(list(filter(lambda x: x != "\r" and len(x) and not re.match(r"^&gt; .*$", x), full_body.split("\n")))[:10])
            truncated_body = author_body[:250] + ("", "...")[len(author_body) > 250]
            message += truncated_body + "\n\n"

        message += "— {} | <a href=\"{}\">Open message</a>".format(self.sender.login, self.comment.html_url)

        await self.send(
            chat_id,
            message,
            'HTML'
        )
