from typing import Annotated
from fastapi import APIRouter, Depends, Path, HTTPException
from pydantic import BaseModel, Field
from starlette import status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from ..database import SessionLocal
from ..models import Todo
from ..routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from fastapi import Request
from dotenv import load_dotenv
import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage , AIMessage
import markdown
from bs4 import BeautifulSoup
import json
import re

router = APIRouter(
    prefix="/todo",
    tags=["Todo"],
)

templates = Jinja2Templates(directory="app/templates")

# ✅ Request Model
class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(gt=0, lt=6)
    completed: bool

class ChatRequest(BaseModel):
    message: str


# ✅ DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ TYPE DOĞRU ŞEKİLDE
DbSession = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_301_MOVED_PERMANENTLY)
    redirect_response.delete_cookie("access_token")
    return redirect_response


@router.get("/todo-page")
async def render_todo_page(request: Request, db: DbSession):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        
        todos = db.query(Todo).filter(Todo.owner_id == user.get('id')).all()
        
        # Calculate Stats
        total = len(todos)
        completed = len([t for t in todos if t.completed])
        pending = total - completed
        rate = int((completed / total) * 100) if total > 0 else 0
        
        stats = {
            "total": total,
            "completed": completed,
            "pending": pending,
            "rate": rate
        }
        
        return templates.TemplateResponse("todo.html", {
            "request": request, 
            "todos": todos, 
            "user": user,
            "stats": stats
        })
    except Exception as e:
        print(f"Error rendering todo page: {e}")
        return redirect_to_login()


@router.get("/add-todo-page")
async def render_add_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-todo.html", {"request": request , "user": user})
    except :
        return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: DbSession):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        return templates.TemplateResponse("edit-todo.html", {"request": request , "todo": todo , "user": user})
    except :
        return redirect_to_login()

# ✅ READ ALL
@router.get("/")
async def read_all(user : user_dependency , db: DbSession):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(Todo).filter(Todo.owner_id == user.get('id')).all()


# ✅ READ BY ID
@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_by_id(user : user_dependency , db: DbSession, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")


# ✅ CREATE
@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user : user_dependency , db: DbSession, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    # Enhance everything with Gemini (with fallback)
    try:
        # Gemini provides: description, priority, subtasks
        ai_data = create_todo_with_gemini(todo_request.title)
        
        enhanced_description = ai_data.get("description", todo_request.description)
        suggested_priority = ai_data.get("priority", todo_request.priority)
        subtask_list = ai_data.get("subtasks", [])
    except Exception as e:
        print(f"Gemini API Error: {e}")
        enhanced_description = todo_request.description
        suggested_priority = todo_request.priority
        subtask_list = []

    todo = Todo(
        title=todo_request.title,
        description=enhanced_description,
        priority=suggested_priority,
        completed=todo_request.completed,
        owner_id=user.get('id')
    )
    db.add(todo)
    db.commit()
    db.refresh(todo) # Get ID for subtasks

    # Save Subtasks
    from models import Subtask
    for sub_content in subtask_list:
        subtask = Subtask(content=sub_content, todo_id=todo.id)
        db.add(subtask)
    db.commit()


# ✅ UPDATE
@router.put("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def update_todo(user : user_dependency , db: DbSession , todo_request: TodoRequest , todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()

    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.completed = todo_request.completed

    db.add(todo)
    db.commit()


# ✅ DELETE
@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user : user_dependency , db: DbSession, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()

    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    db.delete(todo)
    db.commit()


# ✅ TOGGLE STATUS (Hızlı Tamamla)
@router.patch("/todo/{todo_id}/toggle", status_code=status.HTTP_200_OK)
async def toggle_todo_status(user: user_dependency, db: DbSession, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    todo.completed = not todo.completed
    db.add(todo)
    db.commit()
    return {"status": "updated", "completed": todo.completed}


# ⭐ AI ASİSTAN CHAT ENDPOINT
@router.post("/chat", status_code=status.HTTP_200_OK)
async def ai_assistant_chat(user: user_dependency, db: DbSession, chat_request: ChatRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    # Fetch all user todos for context
    todos = db.query(Todo).filter(Todo.owner_id == user.get('id')).all()
    todo_context = "\n".join([f"- {t.title} ({'Bitti' if t.completed else 'Bekliyor'}, Öncelik: {t.priority})" for t in todos])
    
    load_dotenv()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
    
    prompt = f"""
    Sen, ToDoGemini uygulamasının kişisel AI asistanısın. Kullanıcının görev listesi aşağıdadır:
    {todo_context if todos else "Henüz görev yok."}
    
    Kullanıcı sana şunu soruyor: "{chat_request.message}"
    
    Lütfen kullanıcının görevlerini bilerek, motive edici, profesyonel ve kısa bir cevap ver. 
    Eğer liste boşsa, yeni görevler eklemesi için onu teşvik et. Cevabını Türkçe ver.
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"response": response.content}
    except Exception as e:
        print(f"Chat API Error: {e}")
        return {"response": "Üzgünüm, asistan şu an uykuda. Lütfen az sonra tekrar dene."}

def markdown_to_text(markdown_string):
    html = markdown.markdown(markdown_string)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text


def create_todo_with_gemini(todo_string : str):
    load_dotenv()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
    
    prompt = f"""
    Analyze the following todo item: "{todo_string}"
    Create a highly professional and comprehensive response in JSON format (TURKISH language).
    The JSON must have the following fields:
    1. "description": A long, detailed, and motivating description of the task. Keep it clean (no markdown symbols like **).
    2. "priority": Suggest a priority from 1 to 5 (1 is low, 5 is critical/urgent).
    3. "subtasks": A list of 3 to 6 practical action steps to complete this task.
    
    IMPORTANT: Return ONLY the raw JSON object. No chat, no code blocks, no other text.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Extract JSON (sometimes models add ```json ... ```)
    raw_content = response.content
    json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
            
    # Fallback structure
    return {
        "description": raw_content,
        "priority": 3,
        "subtasks": []
    }
