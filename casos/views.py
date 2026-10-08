from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from datetime import date
from .models import Cliente, Caso, EstadoCaso, Expediente, Pago
from .forms import ClienteForm

# --- MANTENEDOR DE CLIENTES ---

def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'casos/cliente_list.html', {'clientes': clientes})

def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'casos/cliente_form.html', {'form': form, 'titulo': 'Nuevo Cliente'})

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'casos/cliente_form.html', {'form': form, 'titulo': 'Editar Cliente'})

def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'casos/cliente_confirm_delete.html', {'cliente': cliente})


# --- VISTAS DE CASOS Y FUNCIONALIDADES DE PREGUNTA 4 ---

def lista_casos(request):
    """
    Listado de casos con filtro por estado mediante GET y persistencia en Cookie.
    """
    estados = EstadoCaso.objects.all()
    estado_id = request.GET.get('estado')

    # Si no se pasó filtro en GET, intentar leer la cookie 'ultimo_estado'
    if not estado_id:
        estado_id = request.COOKIES.get('ultimo_estado')

    casos = Caso.objects.all().select_related('cliente', 'estado').prefetch_related('abogados')

    if estado_id and estado_id != 'todos':
        casos = casos.filter(estado_id=estado_id)

    response = render(request, 'casos/caso_list.html', {
        'casos': casos,
        'estados': estados,
        'estado_seleccionado': str(estado_id) if estado_id else ''
    })

    # Guardar en cookie el último estado consultado
    if request.GET.get('estado'):
        response.set_cookie('ultimo_estado', request.GET.get('estado'), max_age=60*60*24*7) # 7 días

    return response


def detalle_caso(request, pk):
    """
    Muestra el detalle del caso y procesa el registro de pagos y subida de documentos.
    """
    caso = get_object_or_404(Caso, pk=pk)

    # Procesar registro de pago por POST
    if request.method == 'POST' and 'btn_pago' in request.POST:
        if not caso.estado.permite_pagos:
            messages.error(request, f"No se aceptó el pago: El estado '{caso.estado.nombre}' del caso no admite pagos.")
        else:
            try:
                monto = float(request.POST.get('monto', 0))
                descripcion = request.POST.get('descripcion', '')
                if monto > 0:
                    pago = Pago(caso=caso, monto=monto, fecha=date.today(), descripcion=descripcion)
                    pago.full_clean()
                    pago.save()
                    messages.success(request, f"Pago de S/. {monto:.2f} registrado exitosamente.")
                else:
                    messages.error(request, "El monto debe ser mayor a cero.")
            except Exception as e:
                messages.error(request, f"Error al registrar el pago: {e}")
        return redirect('detalle_caso', pk=caso.id)

    # Procesar subida de documento a Expediente por POST
    if request.method == 'POST' and 'btn_documento' in request.POST:
        expediente_id = request.POST.get('expediente_id')
        archivo = request.FILES.get('documento')
        if expediente_id and archivo:
            expediente = get_object_or_404(Expediente, id=expediente_id, caso=caso)
            expediente.documento = archivo
            expediente.save()
            messages.success(request, f"Documento subido correctamente para el Expediente {expediente.numero}.")
        else:
            messages.error(request, "Debe seleccionar un archivo válido.")
        return redirect('detalle_caso', pk=caso.id)

    expedientes = caso.expedientes.all()
    pagos = caso.pagos.all()

    return render(request, 'casos/caso_detail.html', {
        'caso': caso,
        'expedientes': expedientes,
        'pagos': pagos,
    })


def api_caso(request, pk):
    """
    API JSON que retorna el detalle general del caso[cite: 1].
    """
    caso = get_object_or_404(Caso, pk=pk)
    data = {
        'codigo': caso.codigo,
        'cliente': caso.cliente.nombres,
        'estado': caso.estado.nombre,
        'abogados': [a.get_full_name() or a.username for a in caso.abogados.all()],
        'numero_expedientes': caso.expedientes.count(),
        'total_pagado': float(caso.total_pagado()),
    }
    return JsonResponse(data)  # JsonResponse requerido[cite: 1]