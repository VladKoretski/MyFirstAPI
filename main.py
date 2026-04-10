from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(
    title="Task Manager API",
    description="API для создания и получения задач с временным хранением в памяти.",
    version="1.0.0"
)

tasks_db = {}
next_task_id = 1

class TaskCreate(BaseModel):
    title: str = Field(
        ..., 
        min_length=3, 
        max_length=100,
        description="Обязательная строка (String). Ограничение: 3–100 символов. Назначение: краткая идентификация задачи в списках и отчётах."
    )
    description: Optional[str] = Field(
        None,
        description="Необязательное строковое поле (String, допускает null или пустую строку) без жёстких ограничений длины. Назначение: детализация требований, контекста или инструкций для выполнения."
    )
    priority: int = Field(
        ..., 
        ge=1, 
        le=5,
        description="Обязательное целое число (Integer). Ограничение: диапазон 1–5. Назначение: определение порядка обработки и приоритизации в очередях задач."
    )

class TaskResponse(BaseModel):
    id: int = Field(
        ..., 
        description="Уникальный системный идентификатор (Integer). Формат: генерируется сервером автоматически. Назначение: однозначная ссылка на ресурс и ключ для маршрутизации запросов."
    )
    title: str = Field(
        ..., 
        description="Строка (String), возвращаемая в исходном виде. Ограничение: 3–100 символов. Назначение: отображение заголовка задачи в клиентском интерфейсе."
    )
    description: Optional[str] = Field(
        None, 
        description="Строка (String) или null, возвращающая сохранённое значение без модификаций. Назначение: предоставление полного контекста задачи пользователю."
    )
    priority: int = Field(
        ..., 
        description="Целое число (Integer) в диапазоне 1–5. Назначение: визуальная индикация критичности задачи и поддержка клиентской сортировки списков."
    )

@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=201,
    summary="Создание новой задачи",
    description="Инициирует создание задачи в системе с обязательной проверкой входных данных. Поля title и priority обязательны, приоритет задаётся числовой шкалой от 1 до 5. После успешной обработки сервер возвращает полный объект задачи с уникальным id для последующего отслеживания, обновления или привязки к другим ресурсам.",
    responses={
        201: {"description": "Задача успешно создана. В теле ответа возвращается объект задачи с присвоенным системным идентификатором."},
        422: {"description": "Ошибка семантической валидации. Возникает при отсутствии обязательных полей, нарушении длины title (3–100 символов) или выходе значения priority за допустимый диапазон 1–5."}
    }
)
def create_task(task: TaskCreate):
    global next_task_id
    task_data = task.model_dump()
    task_data["id"] = next_task_id
    tasks_db[next_task_id] = task_data
    next_task_id += 1
    return task_data

@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Получение задачи по ID",
    description="Возвращает полную информацию о задаче по её уникальному идентификатору. Используется для отображения деталей в интерфейсе или проверки актуального статуса задачи перед выполнением бизнес-операций. Запрос выполняется напрямую по ключу без дополнительной фильтрации или агрегации.",
    responses={
        200: {"description": "Задача найдена. В теле ответа возвращается объект задачи со всеми её текущими полями."},
        404: {"description": "Запрашиваемый ресурс отсутствует. В Task Manager это означает, что задача с указанным task_id не найдена в хранилище, была удалена или идентификатор передан с опечаткой."}
    }
)
def get_task(task_id: int):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task