import asyncio
import ssl
import logging
import html
from quopri import decodestring


from aiosmtpd.controller import Controller
from email.parser import BytesParser
from nio import AsyncClient

from auth import Authenticator
from config import password
from synapse_admin import get_username


class MySMTPServer:
    async def handle_DATA(self, server, session, envelope):
        parser = BytesParser()
        parse_email = parser.parsebytes(text=envelope.content)
        message = parse_email.get_payload()
        email = envelope.rcpt_tos
        username = await get_username(email[0])
        logging.info(username)
        if username:
            decode_message = decodestring(message)
            decode_html = html.unescape(decode_message.decode())
            get_link = decode_html.split("<!!")[1].strip()
            logging.info(f"link: {get_link}")
            client = AsyncClient(
                "https://matrix.spaceship.im", "@otp:spaceship.im")
            await client.login(password)
            get_room = await client.list_direct_rooms()
            if get_room.rooms.get(username):
                room_id = get_room.rooms[username][0]
            else:
                room_creation = await client.room_create(
                    name="login",
                    is_direct=True,
                    invite=[username]
                )
                room_id = room_creation.room_id
            content = {
                "body": "Login",
                "msgtype": "m.text",
                "magic_link": get_link
            }
            try:
               msg_data =  await client.room_send(room_id,
                                   message_type="m.room.message",
                                   content=content)
               logging.info(msg_data)
               await client.logout()
            except Exception as e:
                logging.error(f"error: {e}")
        return '250 OK'


if __name__ == "__main__":
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('certificate.crt', 'privatekey.key')
    smtp_server = MySMTPServer()
    controller = Controller(
        smtp_server,
        hostname="0.0.0.0",
        port=1025,
        authenticator=Authenticator(),
        auth_required=True,
        auth_require_tls=True,
        require_starttls=True,
        tls_context=context
    )
    try:
        # await smtp_server.login()
        #loop = asyncio.get_event_loop()
        #loop.run_until_complete(controller.start())
        controller.start()
        logging.info("SMTP server listening on port 1025")
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("SMTP server stopped by user")
        controller.stop()