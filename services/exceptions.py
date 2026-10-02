# services/exceptions.py

class ServiceError(Exception):
    """Common error for business logic"""
    def __init__(self, message_to_user: str, internal_description: str = None):
        self.message_to_user = message_to_user # То, что покажем в ТГ
        self.internal_description = internal_description # Оставляем для совместимости с логированием
        # Принудительно устанавливаем текст исключения Python как сообщение для пользователя
        super().__init__(message_to_user)

class InventoryError(ServiceError):
    """Errors connected with warehouses and products"""
    pass

class NotEnoughStockError(InventoryError):
    """Try to clear more than available"""
    def __init__(self):
        super().__init__("⚠️ На складе недостаточно товара для списания.")

class GeneralDBError(ServiceError):
    """General database error that shows technical details in the chat"""
    def __init__(self, internal_description: str):
        # МЫ ИЗМЕНИЛИ ЭТУ СТРОКУ.
        # Теперь техническое описание (SQL ошибка) напрямую включается
        # в сообщение, предназначенное для отправки в Telegram чат.
        message_for_chat = f"❌ Критическая ошибка базы данных.\nПроблема: {internal_description}"
        super().__init__(message_for_chat, internal_description)


class DuplicateError(ServiceError):
    """Базовый класс для дубликатов"""
    pass

class UserAlreadyExistsError(DuplicateError):
    def __init__(self):
        super().__init__("⚠️ Пользователь с таким Telegram ID уже зарегистрирован.")

class ProductAlreadyExistsError(DuplicateError):
    def __init__(self):
        super().__init__("⚠️ Категория товара с таким названием уже существует.")


class NotFoundError(ServiceError):
    """Когда объект не найден в базе"""
    def __init__(self, entity_name: str):
        super().__init__(f"⚠️ {entity_name} не найден(а) в базе данных. Возможно, данные были удалены.")

class RelatedEntityNotFoundError(ServiceError):
    """Когда нарушен внешний ключ (FOREIGN KEY)"""
    def __init__(self):
        super().__init__("⚠️ Невозможно выполнить действие: связанный склад или товар больше не существует.")


class ValidationError(ServiceError):
    """Ошибки некорректного ввода данных"""
    def __init__(self, reason: str):
        super().__init__(f"❌ Отказ операции: {reason}")

class InvalidQuantityError(ValidationError):
    def __init__(self):
        super().__init__("Количество должно быть больше нуля.")


