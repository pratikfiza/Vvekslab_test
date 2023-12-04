from fastapi import FastAPI, Request, HTTPException,Request, File, UploadFile, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dbcon import get_db_connector, select, insert
from sqlalchemy import select,update
import uvicorn
from fastapi.encoders import jsonable_encoder
from  werkzeug.security import check_password_hash
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta

SECRET_KEY = 'secret key'

blacklisted_tokens = []



app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory='templates')

def get_publication_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.line, table.columns.url]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset




def get_book_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.book_name,table.columns.insert_author,table.columns.insert_year,table.columns.insert_publisher,table.columns.insert_isbn, table.columns.article_url]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


def get_bookchapter_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.insert_author,table.columns.insert_year,table.columns.insert_ctitle,table.columns.insert_booktitle,table.columns.insert_editor, table.columns.insert_publisher,table.columns.insert_pageno,table.columns.insert_url]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset

# insert_author,insert_year,insert_ptitle,insert_ctitle,insert_doe,insert_pageno,insert_link

def get_conf_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.insert_author,table.columns.insert_year,table.columns.insert_ptitle,table.columns.insert_ctitle,table.columns.insert_doe,table.columns.insert_pageno, table.columns.insert_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


def get_resource_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.res_id, table.columns.res_heading, table.columns.res_title,table.columns.res_text,table.columns.res_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


def get_journal_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.insert_author, table.columns.insert_year,table.columns.insert_papertitle,table.columns.insert_journalname,table.columns.insert_volume,table.columns.insert_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset

def get_publication_news(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.insert_article, table.columns.insert_author,table.columns.insert_name, table.columns.insert_pubdate, table.columns.insert_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset












def get_all_photos():
    table, engine = get_db_connector('phd_students')
    query = select([table.columns.student_id, table.columns.student_photo_path,table.columns.student_name,table.columns.student_position,]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


@app.get('/publication')
def home(request: Request):
    books = get_book_data('publication_books')
    book_chapters = get_bookchapter_data('publication_book_chapters')
    articles = get_journal_data('publication_journal_articles')
    conference = get_conf_data('publication_conference')
    news_papers = get_publication_news('publication_newspapers')
   

    return templates.TemplateResponse('publication.html',
    context={'request': request,
             'books': books,
             'book_chapters': book_chapters,
             'articles': articles,
             'conference': conference,
             'news_papers': news_papers,
             
             })




@app.get('/teams')
def load_home(request: Request):
   
    data = get_all_photos()
    return templates.TemplateResponse('teams.html',context={'request': request, 'image_paths': data})


@app.get('/research')
def load_home(request: Request):

    return templates.TemplateResponse('reseach.html',context={'request': request})

@app.get('/gallery')
def load_home(request: Request):

    return templates.TemplateResponse('gallery.html',context={'request': request})


@app.get('/contactus')
def load_home(request: Request):

    return templates.TemplateResponse('contactUs.html',context={'request': request})


@app.get('/labnews')
def load_home(request: Request):
    labnews=get_publication_data('news_lab')

    return templates.TemplateResponse('labnews.html',context={'request': request,'labnews':labnews})


# @app.get("/admin")
# def redirect_admin():
#     try:
#         response = RedirectResponse(url="http://localhost:8001/")
#         return response
#     except:
#         raise HTTPException(status_code=500, detail="Internal server error")




@app.get('/logout')
def logout(request: Request, token=''):

    global blacklisted_tokens
    if token:
        blacklisted_tokens.append(token)

    def check_tokens(token):
        try:
            jwt.decode(token, SECRET_KEY)
        except Exception:
            return False
        else:
            return True
    
    blacklisted_tokens = list(filter(check_tokens, blacklisted_tokens))

    return templates.TemplateResponse('signup.html', context={'request': request})


class creds(BaseModel):
    user_name: str
    password: str


@app.post('/validate_credentials')
def check_user(creds: creds):

    creds = jsonable_encoder(creds)


    table, engine = get_db_connector('admin_login')
    query = select([table.columns.public_id, table.columns.password_hash]).where(table.columns.user_name==creds['user_name']).limit(1)

    resultproxy = engine.execute(query)

    db_creds = resultproxy.fetchone()

    if creds:
        public_id, password = db_creds

        if check_password_hash(password, creds['password']):
        
            token = jwt.encode({
                'public_id': public_id,
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }, SECRET_KEY)
    
            return {'success': 'User Validated', 'token': token.decode('UTF-8')}

    
    return {'error': 'Invalid Credentials'}


def get_publication_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.line, table.columns.url]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset



def get_publication_news(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.insert_article, table.columns.insert_author,table.columns.insert_name, table.columns.insert_pubdate, table.columns.insert_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


def get_book_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.book_name,table.columns.insert_author,table.columns.insert_year,table.columns.insert_publisher,table.columns.insert_isbn, table.columns.article_url]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


def get_bookchapter_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.insert_author,table.columns.insert_year,table.columns.insert_ctitle,table.columns.insert_booktitle,table.columns.insert_editor, table.columns.insert_publisher,table.columns.insert_pageno,table.columns.insert_url]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


def get_conf_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.insert_author,table.columns.insert_year,table.columns.insert_ptitle,table.columns.insert_ctitle,table.columns.insert_doe,table.columns.insert_pageno, table.columns.insert_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


def get_resource_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.res_id, table.columns.res_heading, table.columns.res_title,table.columns.res_text,table.columns.res_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


def get_journal_data(table_name):
    table, engine = get_db_connector(table_name)
    query = select([table.columns.id, table.columns.insert_author, table.columns.insert_year,table.columns.insert_papertitle,table.columns.insert_journalname,table.columns.insert_volume,table.columns.insert_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset



class insert_article(BaseModel):
    insert_author: str
    insert_year: str
    insert_papertitle: str
    insert_journalname: str
    insert_volume: str
    insert_link: str

def insert_article_data(insert_author,insert_year,insert_papertitle, insert_journalname ,insert_volume ,insert_link):
    table, engine = get_db_connector('publication_journal_articles')
    query = insert(table).values(insert_author=insert_author, insert_year=insert_year, insert_papertitle=insert_papertitle, insert_journalname=insert_journalname, insert_volume=insert_volume, insert_link=insert_link)
    engine.execute(query)

@app.post("/insert_article")
def add_article(insert_data: insert_article):
    data = jsonable_encoder(insert_data)
    insert_article_data(data['insert_author'], data['insert_year'],data['insert_papertitle'],data['insert_journalname'], data['insert_volume'], data['insert_link'])
    return {'success': 'Article Inserted'}


class update_article(BaseModel):
    id: str
    insert_author: str
    insert_year: str
    insert_papertitle: str
    insert_journalname: str
    insert_volume: str
    insert_link: str

def update_article_data(id,insert_author,insert_year,insert_papertitle, insert_journalname ,insert_volume ,insert_link):
    table, engine = get_db_connector('publication_journal_articles')
    query = update(table).values(insert_author=insert_author, insert_year=insert_year, insert_papertitle=insert_papertitle, insert_journalname=insert_journalname, insert_volume=insert_volume, insert_link=insert_link).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/update_article")
def edit_article(update_data: update_article):
    data=jsonable_encoder(update_data)
    update_article_data(data['id'],data['insert_author'], data['insert_year'],data['insert_papertitle'],data['insert_journalname'], data['insert_volume'], data['insert_link'])
    return {'success': 'Article Updated'}








#Delete Publication Article
class delete_article(BaseModel):
    id: str
 
def delete_article_data(id):
    table, engine = get_db_connector('publication_journal_articles')
    query = update(table).values(is_deleted = 1).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/delete_article")
def edit_article(delete_data: delete_article):
    data=jsonable_encoder(delete_data)
    delete_article_data(data['id'])
    return {'success': 'Article Deleted'}
    


# Books Delete API
class delete_article_book(BaseModel):
    id: str
 

def delete_article_books(id):
    table, engine = get_db_connector('publication_books')
    query = update(table).values(is_deleted = 1).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/delete_article_books")
def delete_article(delete_data: delete_article_book):
    data=jsonable_encoder(delete_data)
    delete_article_books(data['id'])
    return {'success': 'Article Deleted'}


# Edit books API
class update_books(BaseModel):
    id: str
    book_name: str
    insert_author: str
    insert_year:str
    insert_publisher:str
    insert_isbn:str
    article_url:str


def update_books_data(id, book_name,insert_author,insert_year,insert_publisher,insert_isbn, article_url):
    table, engine = get_db_connector('publication_books')
    query = update(table).values(book_name=book_name, insert_author=insert_author,insert_year=insert_year,insert_publisher=insert_publisher,insert_isbn=insert_isbn ,article_url=article_url).where(table.columns.id == id)
    engine.execute(query)

    
@app.post("/update_article_books")
def editbooks_article(update_data: update_books):
    data=jsonable_encoder(update_data)
    update_books_data(data['id'],data['book_name'],data['insert_author'],data['insert_year'],data['insert_publisher'],data['insert_isbn'], data['article_url'])
    return {'success': 'Article Updated'}

#   bookname : $('#insert_book_name').val(),
#                     insert_author : $('#insert_author').val(),
#                     insert_year : $('#insert_year').val(),
#                     insert_publisher : $('#insert_publisher').val(),
#                     insert_isbn : $('#insert_isbn').val(),


# Add Books API
class insert_article_books(BaseModel):
    book_name: str
    insert_author: str
    insert_year:str
    insert_publisher:str
    insert_isbn:str
    article_url:str

def insert_book_data(book_name,insert_author,insert_year,insert_publisher,insert_isbn, article_url):
    table, engine = get_db_connector('publication_books')
    query = insert(table).values(book_name=book_name, insert_author=insert_author,insert_year=insert_year,insert_publisher=insert_publisher,insert_isbn=insert_isbn ,article_url=article_url)

    engine.execute(query)

@app.post("/insert_article_books")
def add_article(insert_data: insert_article_books):
    data = jsonable_encoder(insert_data)
    insert_book_data(data['book_name'],data['insert_author'],data['insert_year'],data['insert_publisher'],data['insert_isbn'], data['article_url'])
    return {'success': 'Article Inserted'}




#Lab News API


class insert_lab_news(BaseModel):
    article_text: str
    article_url: str

def insert_lab_data(article_text, article_url):
    table, engine = get_db_connector('news_lab')
    query = insert(table).values(line=article_text, url=article_url)

    engine.execute(query)

@app.post("/insert_lab_news")
def add_news(insert_data: insert_lab_news):
    data = jsonable_encoder(insert_data)
    insert_book_data(data['article_text'], data['article_url'])
    return {'success': 'Article Inserted'}




@app.get('/redirect_page')
def home(request: Request,token=''):
    
    token_valid = is_valid_token(token)

    if token_valid:
        return templates.TemplateResponse('redirect_page.html', context={'request': request})
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})


    

def is_valid_token(token):

    if token in blacklisted_tokens:
        return False
        
    
    try:
        data = jwt.decode(token, SECRET_KEY)
        public_id = data['public_id']

    except Exception:
        return False

    table, engine = get_db_connector('admin_login')
    query = select(1).where(table.columns.public_id==public_id)

    data = engine.execute(query)

    return bool(data.fetchone())



# Jounal Arcticle Show API 
@app.get('/admin_home')
def admin_home(request: Request, token: str = ''):

    token_valid = is_valid_token(token)

    if token_valid:
        data = get_journal_data('publication_journal_articles')
        return templates.TemplateResponse('show_articles.html', context={'request': request, 'journal_data': data})
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})



# Books Arcticle Show API 
@app.get('/load_books')
def admin_book(request: Request,token=''):
    token_valid = is_valid_token(token)
    if token_valid:
        data = get_book_data('publication_books')
        return templates.TemplateResponse('show_books.html', context={'request': request, 'books_data': data})
    
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})


# Conference Arcticle Show API 
@app.get('/load_conf')
def admin_book(request: Request,token=''):
    token_valid = is_valid_token(token)
    if token_valid:
        data = get_conf_data('publication_conference')
        return templates.TemplateResponse('show_conf.html', context={'request': request, 'books_data': data})
    
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})


#Insert Conference Data

# insert_author,insert_year,insert_ptitle,insert_ctitle,insert_doe,insert_pageno,insert_link


class insert_conf(BaseModel):
    insert_author: str
    insert_year: str
    insert_ptitle: str
    insert_ctitle: str
    insert_doe: str
    insert_pageno: str
    insert_link: str
    


def insert_article_conf(insert_author,insert_year,insert_ptitle,insert_ctitle,insert_doe,insert_pageno,insert_link):
    table, engine = get_db_connector('publication_conference')
    query = insert(table).values(insert_author=insert_author,insert_year=insert_year,insert_ptitle=insert_ptitle,insert_ctitle=insert_ctitle,insert_doe=insert_doe,insert_pageno=insert_pageno,insert_link=insert_link)

    engine.execute(query)

@app.post("/insert_conf")
def add_article(insert_data: insert_conf):
    data = jsonable_encoder(insert_data)
    insert_article_conf(data['insert_author'], data['insert_year'],data['insert_ptitle'], data['insert_ctitle'],data['insert_doe'], data['insert_pageno'],data['insert_link'])
    return {'success': 'Conference Inserted'}





#Update Conference Data
class update_conf(BaseModel):
    id: str
    insert_author: str
    insert_year: str
    insert_ptitle: str
    insert_ctitle: str
    insert_doe: str
    insert_pageno: str
    insert_link: str

def update_conf_data(id,insert_author,insert_year,insert_ptitle,insert_ctitle,insert_doe,insert_pageno,insert_link):
    table, engine = get_db_connector('publication_conference')
    query = update(table).values(insert_author=insert_author,insert_year=insert_year,insert_ptitle=insert_ptitle,insert_ctitle=insert_ctitle,insert_doe=insert_doe,insert_pageno=insert_pageno,insert_link=insert_link).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/update_conf")
def edit_article(update_data: update_conf):
    data=jsonable_encoder(update_data)
    update_conf_data(data['id'], data['insert_author'], data['insert_year'],data['insert_ptitle'], data['insert_ctitle'],data['insert_doe'], data['insert_pageno'],data['insert_link'])
    return {'success': 'Conference Updated'}





#Conference Delete API
class delete_conf(BaseModel):
    id: str
 

def delete_article_conf(id):
    table, engine = get_db_connector('publication_conference')
    query = update(table).values(is_deleted = 1).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/delete_conf")
def delete_article(delete_data: delete_conf):
    data=jsonable_encoder(delete_data)
    delete_article_conf(data['id'])
    return {'success': 'Conference Deleted'}











# Bookchapter Show API 
@app.get('/load_books_chapter')
def admin_bookchapter(request: Request,token=''):
    token_valid = is_valid_token(token)
    if token_valid:
        data = get_bookchapter_data('publication_book_chapters')
        return templates.TemplateResponse('show_bookchapter.html', context={'request': request, 'books_data': data})
    
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})




#   insert_author : $('#insert_author-'+id).val(),
#                     insert_year : $('#insert_year-'+id).val(),
#                     insert_ctitle : $('#insert_ctitle-'+id).val(),
#                     insert_booktitle : $('#insert_booktitle-'+id).val(),
#                     insert_editor : $('#insert_editor-'+id).val(),
#                     insert_publisher : $('#insert_publisher-'+id).val(),
#                     insert_pageno : $('#insert_pageno-'+id).val(),
#                     insert_url : $('#insert_url-'+id).val(),



#Insert Bookchapter Data

class insert_bookchapter(BaseModel):
    insert_author: str
    insert_year: str
    insert_ctitle: str
    insert_booktitle: str
    insert_editor: str
    insert_publisher: str
    insert_pageno: str
    insert_url: str

def insert_article_bookchapter(insert_author, insert_year,insert_ctitle,insert_booktitle,insert_editor,insert_publisher,insert_pageno,insert_url):
    table, engine = get_db_connector('publication_book_chapters')
    query = insert(table).values(insert_author=insert_author, insert_year=insert_year,insert_ctitle=insert_ctitle,insert_booktitle=insert_booktitle,insert_editor=insert_editor,insert_publisher=insert_publisher,insert_pageno=insert_pageno,insert_url=insert_url)

    engine.execute(query)

@app.post("/insert_bookchapter")
def add_article(insert_data: insert_bookchapter):
    data = jsonable_encoder(insert_data)
    insert_article_bookchapter(data['insert_author'], data['insert_year'],data['insert_ctitle'], data['insert_booktitle'],data['insert_editor'], data['insert_publisher'],data['insert_pageno'],data['insert_url'])
    return {'success': 'Book chapter Inserted'}





#Update Bookchapter Data
class update_bookchapter(BaseModel):
    id: str
    insert_author: str
    insert_year: str
    insert_ctitle: str
    insert_booktitle: str
    insert_editor: str
    insert_publisher: str
    insert_pageno: str
    insert_url: str

def update_bookchapters(id, insert_author, insert_year,insert_ctitle,insert_booktitle,insert_editor,insert_publisher,insert_pageno,insert_url):
    table, engine = get_db_connector('publication_book_chapters')
    query = update(table).values(insert_author=insert_author, insert_year=insert_year,insert_ctitle=insert_ctitle,insert_booktitle=insert_booktitle,insert_editor=insert_editor,insert_publisher=insert_publisher,insert_pageno=insert_pageno,insert_url=insert_url).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/update_bookchapter")
def edit_article(update_data: update_bookchapter):
    data=jsonable_encoder(update_data)
    update_bookchapters(data['id'],data['insert_author'], data['insert_year'],data['insert_ctitle'], data['insert_booktitle'],data['insert_editor'], data['insert_publisher'],data['insert_pageno'],data['insert_url'])
    return {'success': 'Book chapter Updated'}





#Bookchapter Delete API
class delete_bookchapter(BaseModel):
    id: str
 

def delete_article_bookchapter(id):
    table, engine = get_db_connector('publication_book_chapters')
    query = update(table).values(is_deleted = 1).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/delete_bookchapter")
def delete_article(delete_data: delete_bookchapter):
    data=jsonable_encoder(delete_data)
    delete_article_bookchapter(data['id'])
    return {'success': 'Book Chapter Deleted'}













# Resources Show API 
@app.get('/load_resources')
def admin_bookchapter(request: Request,token=''):
    token_valid = is_valid_token(token)
    if token_valid:
        data = get_resource_data('resources')
        return templates.TemplateResponse('resources.html', context={'request': request, 'books_data': data})
    
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})


# #Insert Bookchapter Data

class insert_resources(BaseModel):
    res_heading: str
    res_title: str
    res_text:str
    res_link:str
 

def insert_resources_fun(res_heading,res_title, res_text,res_link):
    table, engine = get_db_connector('resources')
    query = insert(table).values(res_heading=res_heading, res_title=res_title,res_text=res_text,res_link=res_link)

    engine.execute(query)

@app.post("/insert_resources")
def add_resources(insert_data: insert_resources):
    data = jsonable_encoder(insert_data)
    insert_resources_fun(data['res_heading'], data['res_title'],data['res_text'],data['res_link'])
    return {'success': 'Resource Inserted'}



    

#Update Bookchapter Data
class update_resources(BaseModel):
    res_id:str
    res_heading: str
    res_title: str
    res_text:str
    res_link:str

def update_resource_fun(res_id, res_heading,res_title, res_text,res_link):
    table, engine = get_db_connector('resources')
    query = update(table).values(res_heading=res_heading,res_title=res_title, res_text=res_text,res_link=res_link).where(table.columns.res_id == res_id)
    engine.execute(query)
    
@app.post("/update_resources")
def edit_article(update_data: update_resources):
    data=jsonable_encoder(update_data)
    update_resource_fun(data['res_id'], data['res_heading'], data['res_title'], data['res_text'], data['res_link'])
    return {'success': 'Book chapter Updated'}






#Bookchapter Delete API
class delete_resources(BaseModel):
    id: str
 

def delete_resources_fun(id):
    table, engine = get_db_connector('resources')
    query = update(table).values(is_deleted = 1).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/delete_bookchapter")
def delete_article(delete_data: delete_bookchapter):
    data=jsonable_encoder(delete_data)
    delete_article_bookchapter(data['id'])
    return {'success': 'Book Chapter Deleted'}
























# Newspaper Show API 
@app.get('/load_pub_news')
def admin_bookchapter(request: Request,token=''):
    token_valid = is_valid_token(token)
    if token_valid:
        data = get_publication_news('publication_newspapers')
        return templates.TemplateResponse('show_pubnews.html', context={'request': request, 'books_data': data})
    
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})


#Insert Bookchapter Data
# insert_article,insert_author,insert_name,insert_pubdate,insert_link
class insert_newspaper(BaseModel):
    insert_article: str
    insert_author: str
    insert_name: str
    insert_pubdate: str
    insert_link: str
 

def insert_article_news(insert_article,insert_author,insert_name,insert_pubdate,insert_link):
    table, engine = get_db_connector('publication_newspapers')
    query = insert(table).values(insert_article=insert_article,insert_author=insert_author,insert_name=insert_name,insert_pubdate=insert_pubdate,insert_link=insert_link)
    engine.execute(query)

@app.post("/insert_pubnews")
def add_article(insert_data: insert_newspaper):
    data = jsonable_encoder(insert_data)
    insert_article_news(data['insert_article'], data['insert_author'],data['insert_name'], data['insert_pubdate'],data['insert_link'])
    return {'success': 'Newspaper Inserted'}





#Update Bookchapter Data
class update_article_news(BaseModel):
    id: str
    insert_article: str
    insert_author: str
    insert_name: str
    insert_pubdate: str
    insert_link: str

def update_pubnews(id,insert_article,insert_author,insert_name,insert_pubdate,insert_link):
    table, engine = get_db_connector('publication_newspapers')
    query = update(table).values(insert_article=insert_article,insert_author=insert_author,insert_name=insert_name,insert_pubdate=insert_pubdate,insert_link=insert_link).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/update_pubnews")
def edit_article(update_data: update_article_news):
    data=jsonable_encoder(update_data)
    update_pubnews(data['id'],data['insert_article'], data['insert_author'],data['insert_name'], data['insert_pubdate'],data['insert_link'])
    return {'success': 'Newspaper Updated'}





#Bookchapter Delete API
class delete_pubnews(BaseModel):
    id: str
 

def delete_article_pubnews(id):
    table, engine = get_db_connector('publication_newspapers')
    query = update(table).values(is_deleted = 1).where(table.columns.id == id)
    engine.execute(query)
    
@app.post("/delete_pubnews")
def delete_article(delete_data: delete_pubnews):
    data=jsonable_encoder(delete_data)
    delete_article_pubnews(data['id'])
    return {'success': 'Book Chapter Deleted'}




















# Lab News Show API 
@app.get('/load_news')
def admin_book(request: Request,token=''):
    token_valid = is_valid_token(token)
    if token_valid:
        data = get_publication_data('news_lab')
        return templates.TemplateResponse('show_news.html', context={'request': request, 'books_data': data})
    
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})




# Lab News Show API 
@app.get('/load_labalumnis')
def admin_book(request: Request,token=''):
    token_valid = is_valid_token(token)
    if token_valid:
        data = get_publication_data('lab_alumnis')
        return templates.TemplateResponse('show_labalumnis.html', context={'request': request, 'books_data': data})
    
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})








#Show Intern API

def get_all_intern_data():
    table, engine = get_db_connector('intern')
    query = select([table.columns.student_id, table.columns.student_name, table.columns.student_position, table.columns.student_photo_path]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset

@app.get("/team_intern")
def show_team(request: Request, token: str = ''):

    token_valid = is_valid_token(token)

    if token_valid:
        data = get_all_intern_data()

        return templates.TemplateResponse('show_intern.html', context={'request': request, 'intern_data': data})
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})

















# Teams data API

def get_all_students_data():
    table, engine = get_db_connector('phd_students')
    query = select([table.columns.student_id, table.columns.student_name, table.columns.student_position, table.columns.student_photo_path]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset

@app.get("/team")
def show_team(request: Request, token: str = ''):

    token_valid = is_valid_token(token)

    if token_valid:
        data = get_all_students_data()

        return templates.TemplateResponse('show_students.html', context={'request': request, 'students_data': data})
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})


    


class update_student(BaseModel):
    id: str
    student_name: str
    student_positon: str


def update_student_data(id, student_name, student_position, file_path):
    table, engine = get_db_connector('phd_students')
    query = update(table).values(student_name=student_name, student_position=student_position, student_photo_path=file_path).where(table.columns.student_id == id)

    engine.execute(query)

 

@app.post("/update_student")
def update_student(request: Request, student_data : update_student = Depends(), student_image:UploadFile=File(...)):
    data = jsonable_encoder(student_data)

    # student_image.file.read()

    id = data['id']
    student_name = data['student_name']
    student_position = data['student_positon']

    file_name = student_image.filename

    file_bytes = student_image.file.read()

    file_path = f'assets/images/phd_students/{file_name}'

    with open('static/'+file_path, 'wb') as w:
        w.write(file_bytes)

    update_student_data(id, student_name, student_position, file_path)

    



class delete_student(BaseModel):
    id: str

def delete_student_db(id):
    table, engine = get_db_connector('phd_students')
    query = update(table).values(is_deleted = 1).where(table.columns.student_id == id)
    engine.execute(query)

@app.post("/delete_student")
def delete_student(request: Request, delete_id:delete_student):
    
    data = jsonable_encoder(delete_id)
    id = data['id']

    delete_student_db(id)
    




class insert_student(BaseModel):
    student_name: str
    student_positon: str


def insert_student_data(student_name, student_position, file_path):
    table, engine = get_db_connector('phd_students')
    query = insert(table).values(student_name=student_name, student_position=student_position, student_photo_path=file_path)

    engine.execute(query)


@app.post("/insert_student")
def insert_student(request: Request, student_data : insert_student = Depends(), student_image:UploadFile=File(...)):
    data = jsonable_encoder(student_data)

    # student_image.file.read()

    student_name = data['student_name']
    student_position = data['student_positon']
    

    file_name = student_image.filename

    file_bytes = student_image.file.read()

    file_path = f'assets/images/phd_students/{file_name}'

    with open('static/'+file_path, 'wb') as w:
        w.write(file_bytes)

    insert_student_data( student_name, student_position, file_path)

    






class insert_photo(BaseModel):
    photo_id: str


def insert_student_photo( photo_id, photo_path):
    table, engine = get_db_connector('phd_students')
    query = insert(table).values(photo_id=photo_id, photo_path=photo_path)

    engine.execute(query)

def get_all_photos():
    table, engine = get_db_connector('gallery')
    query = select([table.columns.photo_id, table.columns.photo_path]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset



#Gallery API

@app.get("/gallery")
def show_gallery(request: Request,token=''):

    token_valid = is_valid_token(token)

    if token_valid:
        data = get_all_photos()
        return templates.TemplateResponse('gallery.html', context={'request': request, 'image_paths': data})
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})
    

def insert_photo(file_path):
    table, engine = get_db_connector('gallery')
    query = insert(table).values(photo_path=file_path)

    engine.execute(query)

@app.post('/insert_student_photo')
def add_photo(student_image:UploadFile=File(...)):
    file_name = student_image.filename

    file_bytes = student_image.file.read()

    file_path = f'assets/images/phd_students/{file_name}'

    with open('static/'+file_path, 'wb') as w:
        w.write(file_bytes)

    insert_student_photo(file_path)



@app.post('/insert_photo')
def add_photo(student_image:UploadFile=File(...)):
    file_name = student_image.filename

    file_bytes = student_image.file.read()

    file_path = f'assets/images/phd_students/{file_name}'

    with open('static/'+file_path, 'wb') as w:
        w.write(file_bytes)

    insert_photo(file_path)

class delete_photo(BaseModel):
    id: str

def delete_photo_db(id):
    table, engine = get_db_connector('gallery')
    query = update(table).values(is_deleted = 1).where(table.columns.photo_id == id)
    engine.execute(query)

@app.post("/delete_photo")
def delete_image(photo_id: delete_photo):
    id = jsonable_encoder(photo_id)['id']

    delete_photo_db(id)




# @app.post("/gallery")
# def insert_student(request: Request, upload_photo : insert_photo = Depends(), student_image:UploadFile=File(...)):
#     data = jsonable_encoder(upload_photo)

#     # student_image.file.read()

#     photo_id = data['student_name']

#     file_name = student_image.filename

#     file_bytes = student_image.file.read()

#     file_path = f'assets/images/phd_students/{file_name}'

#     with open('static/'+file_path, 'wb') as w:
#         w.write(file_bytes)

#     insert_student_data( student_name, student_position, file_path)



    # return templates.TemplateResponse('show_students.html', context={'request': request, 'students_data': data})



@app.get("/admin")
def home_page(request: Request):
    return templates.TemplateResponse('signup.html', context={'request': request})





@app.get('/')
def load_home(request: Request):

    return templates.TemplateResponse('index.html',context={'request': request})


if __name__ == "__main__":
    uvicorn.run('backend:app', host='localhost', port=8003, reload=True)