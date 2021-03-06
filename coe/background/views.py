#Imports Django
from django.shortcuts import render

#Imports de la appa
from .models import Progress_Links

# Create your views here.
def lista_background(request):
    tasks = Progress_Links.objects.all()
    return render(request, 'lista_background.html', {
        'tasks': tasks,
        "refresh": True,
        'has_table': True,
        }
    )

def ver_background(request, task_id=None, task_name=None):
    if task_id:
        task = Progress_Links.objects.get(pk=task_id)
    elif task_name:
        task = Progress_Links.objects.get(tarea=task_name)
    return render(request, 'ver_background.html', {
        "task": task,
        "refresh": True }
    )