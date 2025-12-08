=================
PROJECT STRUCTURE
=================
chatbot_project/
│
├── chatbot_project/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── user_app/               
│   ├── views.py
│   ├── urls.py
│   ├── models.py
│   └── serializers.py
│
├── admin_app/               
│   ├── views.py
│   ├── models.py
│   └── admin.py
│
├── chatbot_app/             
│   ├── views.py
│   ├── urls.py
│   ├── services.py
│
├── ml_app/                 
│   ├── train_model.py
│   ├── predict.py
│   └── ml_model.pkl
│
├── rag_app/                
│   ├── document_loader.py
│   ├── vector_store.py
│   ├── retriever.py
│
├── llm_app/                
│   ├── llm_client.py
│   └── response_generator.py
│
├── database/               
│   ├── db_config.py
│
├── frontend/               
│   ├── src/
│   │   ├── App.js
│   │   ├── ChatUI.js
│   │   └── api.js
│
├── manage.py
└── requirements.txt

========================
COMPLETE SYSTEM WORKFLOW
========================
User → React UI  
        ↓  
Django API  
        ↓  
ML predicts intent  
        ↓  
RAG retrieves documents  
        ↓  
Vector DB finds best match  
        ↓  
LLM generates reply  
        ↓  
Auto reply sent back to user

