from typing import List, Optional
from fastapi import Request

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        
    async def load_data(self):
        form = await self.request.form()
        self.username = form.get('username')
        self.password = form.get('password')
        
    async def is_valid(self):
        if not self.username:
            self.errors.append('Username is required')
        if not self.password:
            self.errors.append('A Valid password is required')
        if not self.errors:
            return True
        return False
        