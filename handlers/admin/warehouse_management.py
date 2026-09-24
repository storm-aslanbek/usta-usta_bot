from aiogram import Router, F
from aiogram.filters import CommandStart, Command, BaseFilter, callback_data
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, WebAppInfo, CallbackQuery

from aiogram.fsm.state import State, StatesGroup

from services import warehouse_services, user_services, inventory_services

import keyboards as kb

from admin_handler import admin_router
from admin_handler import IsAdmin


