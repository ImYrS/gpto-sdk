"""
    @Author: ImYrS Yang
    @Date: 2023/5/8
    @Copyright: @ImYrS
"""

from typing import Optional
from time import time
import logging

import requests


class App:
    """
    GPT+ Open Platform SDK
    """

    def __init__(
            self,
            model: str,
            app_id: Optional[str] = None,
            app_key: Optional[str] = None,
            access_token: Optional[str] = None,
            access_token_expired_at: Optional[int] = None,
            endpoint: Optional[str] = 'https://open.ss.chat/v1',
    ):
        """
        初始化 SDK

        :param model: 模型名称
        :param app_id: 应用 ID
        :param app_key: 应用 Key
        :param access_token: 访问令牌
        :param access_token_expired_at: 访问令牌过期时间
        :param endpoint: API 端点, 默认为 https://open.ss.chat/v1
        """
        self.endpoint = endpoint
        self.app_id = app_id
        self.app_key = app_key
        self.access_token: str = access_token or ''
        self.access_token_expired_at: int = access_token_expired_at or 0
        self.model = model
        self.conversation: Optional[str] = None

        if not self.access_token or not self.access_token_expired_at:
            self.get_access_token()

    def __requests(
            self,
            method: str,
            path: str,
            json: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        发送请求

        :param method: 请求方法
        :param path: 请求路径
        :param json: 请求数据
        :return: 正确响应时返回 data 字段，否则抛出 requests 异常
        """
        if self.access_token and self.access_token_expired_at < int(time() - 60):
            self.access_token = ''
            self.access_token_expired_at = 0
            result = self.get_access_token()
            if not result:
                return

        r = requests.request(
            method=method,
            url=self.endpoint + path,
            json=json,
            headers={'Authorization': 'Bearer ' + self.access_token} if self.access_token else None,
        )
        data = r.json()

        if data['code'] != 200:
            logging.error(f'请求失败: {data}')
            r.raise_for_status()

        return data['data']

    def get_access_token(self) -> Optional[dict]:
        """
        获取 access_token, 同时更新实例属性

        :return: 请求成功时返回 access_token，否则返回 None
        """
        try:
            req = self.__requests(
                method='POST',
                path='/sessions',
                json={
                    'app_id': self.app_id,
                    'app_key': self.app_key,
                },
            )
        except requests.exceptions.RequestException as e:
            logging.error(f'获取 access_token 失败: {e}')
            return

        self.access_token = req['access_token']
        self.access_token_expired_at = int(time()) + req['expires_in']

        return req

    def create_conversation(self, prompt: Optional[str] = None) -> Optional[str]:
        """
        创建对话, 并更新实例属性

        :param prompt: 对话提示词
        :return: 请求成功时返回对话 uuid，否则返回 None
        """
        payload = {'model': self.model}
        if prompt:
            payload['prompt'] = prompt

        try:
            req = self.__requests(
                method='POST',
                path='/conversations',
                json=payload,
            )
        except requests.exceptions.RequestException as e:
            logging.error(f'创建对话失败: {e}')
            return

        self.conversation = req['uuid']

        return self.conversation

    def create_message(
            self,
            content: str,
            prompt: Optional[str] = '',
            max_tokens: Optional[int] = None,
    ) -> Optional[dict]:
        """
        生成回复, 当前实例中不存在对话时会自动创建对话

        :param content: 消息
        :param prompt: 对话提示词, 仅当前实例中不存在对话时有效
        :param max_tokens: 最大生成长度, 默认不限制
        :return: 请求成功时返回响应数据, 否则返回 None
        """
        path = (
            f'/conversations/{self.conversation}/messages'
            if self.conversation else
            '/messages'
        )

        payload = {
            'content': content,
            'model': self.model,
        }

        if path == '/messages':
            payload['prompt'] = prompt

        if max_tokens:
            payload['max_tokens'] = max_tokens

        try:
            req = self.__requests(
                method='POST',
                path=path,
                json=payload,
            )
        except requests.exceptions.RequestException as e:
            logging.error(f'生成回复失败: {e}')
            return

        return req
