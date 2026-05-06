from asgiref.sync import sync_to_async
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from apps.sementicsearch.services.mail_retriever import RAG_Gmail
from apps.sementicsearch.services.vectorizer import Vectorization

def check_user(request):
    user = request.user
    print("Is user authenticated:", user.is_authenticated)
    return user

async def home(request):
    user = await sync_to_async(check_user)(request)
    if not user.is_authenticated:
        return redirect("/auth/login")

    if request.method == 'POST':
        data = request.POST
        
        if 'ingest' in data:
            rag_obj = RAG_Gmail(user)
            results = await rag_obj.read_emails()
            vect = Vectorization(user)
            results = vect.find_data()
        
        if 'find' in data:
            vect = Vectorization(user)
            results = vect.find_data(data['query'])
    else:
        vect = Vectorization(user)
        results = vect.find_data()
    return await sync_to_async(render)(
        request, 
        'index.html',
        {"items": results}
    )