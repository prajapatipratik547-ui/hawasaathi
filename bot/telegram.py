import asyncio
import os
import time
import httpx
from typing import Optional

# the request never reached Telegram, so it's safe to retry these once
RETRY_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout)


def _check(method: str, r: httpx.Response) -> dict:
    # Telegram's request URL contains the bot token, so errors only say the method,
    # the status code and Telegram's own description, never the URL
    if r.status_code >= 400:
        try:
            description = r.json().get("description", "")
        except ValueError:
            description = ""
        raise RuntimeError(f"Telegram {method} failed: HTTP {r.status_code} {description}".strip())
    return r.json()


class Telegram:
    def __init__(self, token: Optional[str] = None):
        # the token is only read when a call is made, so importing the app never needs it
        self._token = token

    @property
    def base(self) -> str:
        token = self._token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
        return f"https://api.telegram.org/bot{token}"

    async def _post(self, method: str, payload: dict) -> dict:
        for attempt in (1, 2):
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(f"{self.base}/{method}", json=payload, timeout=10.0)
                break
            except RETRY_ERRORS as e:
                if attempt == 2:
                    raise RuntimeError(f"Telegram {method} failed: {type(e).__name__}") from None
                await asyncio.sleep(1)
            except httpx.HTTPError as e:
                raise RuntimeError(f"Telegram {method} failed: {type(e).__name__}") from None
        return _check(method, r)

    def _post_sync(self, method: str, payload: dict, files: Optional[dict] = None) -> dict:
        for attempt in (1, 2):
            try:
                if files:
                    # file uploads go as multipart form data
                    r = httpx.post(f"{self.base}/{method}", data=payload, files=files, timeout=30.0)
                else:
                    r = httpx.post(f"{self.base}/{method}", json=payload, timeout=10.0)
                break
            except RETRY_ERRORS as e:
                if attempt == 2:
                    raise RuntimeError(f"Telegram {method} failed: {type(e).__name__}") from None
                time.sleep(1)
            except httpx.HTTPError as e:
                raise RuntimeError(f"Telegram {method} failed: {type(e).__name__}") from None
        return _check(method, r)

    async def send_message(self, chat_id: int, text: str, inline_keyboard: Optional[list] = None, reply_markup_request_location: bool = False, remove_keyboard: bool = False, location_button_text: str = "Share location"):
        payload = {"chat_id": chat_id, "text": text}

        # inline keyboard (e.g. language buttons)
        if inline_keyboard:
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

        # request location via reply keyboard
        if reply_markup_request_location:
            payload["reply_markup"] = {
                "keyboard": [[{"text": location_button_text, "request_location": True}]],
                "one_time_keyboard": True,
                "resize_keyboard": True,
            }

        # remove the custom keyboard
        if remove_keyboard:
            payload["reply_markup"] = {"remove_keyboard": True}

        return await self._post("sendMessage", payload)

    async def set_webhook(self, url: str, secret_token: Optional[str] = None):
        payload = {"url": url}
        if secret_token:
            payload["secret_token"] = secret_token
        return await self._post("setWebhook", payload)

    async def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None):
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        return await self._post("answerCallbackQuery", payload)

    async def download_file(self, file_id: str) -> bytes:
        """The bytes of a file a user sent (e.g. a voice message). Bots can download files up to 20 MB."""
        path = (await self._post("getFile", {"file_id": file_id}))["result"]["file_path"]
        # files live at https://api.telegram.org/file/bot<token>/<path>; the URL holds the token, so keep it out of errors
        url = self.base.replace("/bot", "/file/bot", 1) + "/" + path
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=30.0)
        except httpx.HTTPError as e:
            raise RuntimeError(f"Telegram file download failed: {type(e).__name__}") from None
        if r.status_code >= 400:
            raise RuntimeError(f"Telegram file download failed: HTTP {r.status_code}")
        return r.content

    async def send_chat_action(self, chat_id: int, action: str = "typing"):
        # shows "typing..." for a few seconds, or until we send a message
        return await self._post("sendChatAction", {"chat_id": chat_id, "action": action})

    async def edit_message_text(self, chat_id: int, message_id: int, text: str):
        # sending no reply_markup also removes the message's inline buttons
        return await self._post("editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": text})

    async def remove_buttons(self, chat_id: int, message_id: int):
        payload = {"chat_id": chat_id, "message_id": message_id, "reply_markup": {"inline_keyboard": []}}
        return await self._post("editMessageReplyMarkup", payload)

    # synchronous convenience methods for scripts
    def send_message_sync(self, chat_id: int, text: str, inline_keyboard: Optional[list] = None, reply_markup_request_location: bool = False):
        payload = {"chat_id": chat_id, "text": text}
        if inline_keyboard:
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}
        if reply_markup_request_location:
            payload["reply_markup"] = {
                "keyboard": [[{"text": "Share location", "request_location": True}]],
                "one_time_keyboard": True,
                "resize_keyboard": True,
            }
        return self._post_sync("sendMessage", payload)

    def set_webhook_sync(self, url: str, secret_token: Optional[str] = None):
        payload = {"url": url, "allowed_updates": ["message", "callback_query"]}
        if secret_token:
            payload["secret_token"] = secret_token
        return self._post_sync("setWebhook", payload)

    def delete_webhook_sync(self):
        return self._post_sync("deleteWebhook", {})

    def get_webhook_info_sync(self):
        return self._post_sync("getWebhookInfo", {})
