import json
import logging
from sdk.codexbot_sdk import CodexBot
from config import APPLICATION_TOKEN, APPLICATION_NAME, DB, URL, SERVER
from commands.help import CommandHelp
from commands.start import CommandStart
from events.ping import EventPing
from events.push import EventPush
from events.issues import EventIssues
from github.config import USERS_COLLECTION_NAME


class Github:

    def __init__(self):

        self.sdk = CodexBot(APPLICATION_NAME, SERVER['host'], SERVER['port'], db_config=DB, token=APPLICATION_TOKEN)

        self.sdk.log("Github module initialized")

        self.sdk.register_commands([
            ('github_help', 'help', CommandHelp(self.sdk).help),
            ('github_start', 'start', CommandStart(self.sdk).start)
        ])

        self.sdk.set_routes([
            ('POST', '/github/{user_token}', self.github_callback_handler)
        ])

        self.sdk.set_path_to_static('/img', 'static/img')

        self.sdk.start_server()

    @CodexBot.http_response
    async def github_callback_handler(self, request):

        # Check for route-token passed
        if 'user_token' not in request['params']:
            self.sdk.log("GitHub route handler: user_token is missed")
            return {
                'status': 404
            }

        # Get user data from DB by user token passed in URL
        user_token = request['params']['user_token']
        registered_chat = self.sdk.db.find_one(USERS_COLLECTION_NAME, {'user': user_token})

        # Check if chat was registered
        if not registered_chat or 'chat' not in registered_chat:
            self.sdk.log("GitHub route handler: wrong user token passed")
            return {
                'status': 404
            }

        event_name = request['headers']['X-Github-Event']

        events = {
            'ping': EventPing(self.sdk),
            'push': EventPush(self.sdk),
            'issues': EventIssues(self.sdk)
        }

        if event_name not in events:
            self.sdk.log("Github webhook callback: unsupported event taken: {}".format(event_name))
            return {
                'status': 404
            }

        try:
            # GitHub always pass JSON as request body
            payload = json.loads(request['text'])

            # Call event handler
            await events[event_name].process(payload, registered_chat['chat'])

            return {
                'text': 'OK',
                'status': 200
            }

        except Exception as e:
            self.sdk.log('Cannot handle request from GitHub: {}'.format(e))
            return {
                'status': 404
            }



if __name__ == "__main__":
    github = Github()
