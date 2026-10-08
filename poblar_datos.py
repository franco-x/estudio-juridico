import os
import django
from datetime import date

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'estudio.settings')
django.setup()

from django.contrib.auth.models import User, Group
from casos.models import PerfilAbogado, Cliente, EstadoCaso, Caso, Expediente, Pago

def poblar():
    print("Iniciando la creación de datos de prueba...")

    # 1. Crear Grupo 'Abogados'
    grupo_abogados, created = Group.objects.get_or_create(name='Abogados')
    if created:
        print("-> Grupo 'Abogados' creado correctamente.")

    # 2. Crear Usuarios Abogados con su PerfilAbogado
    abogados_datos = [
        {
            'username': 'abogado_carlos',
            'first_name': 'Carlos',
            'last_name': 'Mendoza',
            'email': 'carlos@vargas.com',
            'colegiatura': 'CAL-10023',
            'especialidad': 'Derecho Civil'
        },
        {
            'username': 'abogado_ana',
            'first_name': 'Ana',
            'last_name': 'Torres',
            'email': 'ana@vargas.com',
            'colegiatura': 'CAL-10088',
            'especialidad': 'Derecho Laboral'
        }
    ]

    usuarios_abogados = []
    for datos in abogados_datos:
        user, u_created = User.objects.get_or_create(
            username=datos['username'],
            defaults={
                'first_name': datos['first_name'],
                'last_name': datos['last_name'],
                'email': datos['email'],
                'is_staff': True  # Para que puedan ingresar al panel si fuera necesario
            }
        )
        if u_created:
            user.set_password('Abogado2026!')
            user.save()
            user.groups.add(grupo_abogados)
            PerfilAbogado.objects.create(
                usuario=user,
                numero_colegiatura=datos['colegiatura'],
                especialidad=datos['especialidad']
            )
            print(f"-> Abogado {user.username} creado y agregado al grupo 'Abogados'.")
        usuarios_abogados.append(user)

    # 3. Crear Estados de Caso
    e_iniciado, _ = EstadoCaso.objects.get_or_create(nombre='iniciado', defaults={'permite_pagos': True})
    e_proceso, _ = EstadoCaso.objects.get_or_create(nombre='en proceso', defaults={'permite_pagos': True})
    e_cancelado, _ = EstadoCaso.objects.get_or_create(nombre='cancelado', defaults={'permite_pagos': False})
    e_terminado, _ = EstadoCaso.objects.get_or_create(nombre='terminado', defaults={'permite_pagos': False})
    e_archivado, _ = EstadoCaso.objects.get_or_create(nombre='archivado', defaults={'permite_pagos': False})
    print("-> Estados del caso creados/verificados (iniciado, en proceso, cancelado, terminado, archivado).")

    # 4. Crear Cliente
    cliente, _ = Cliente.objects.get_or_create(
        documento='20601234567',
        defaults={
            'nombres': 'Corporación Inmobiliaria S.A.C.',
            'telefono': '987654321',
            'correo': 'contacto@inmobiliaria.com'
        }
    )
    print(f"-> Cliente '{cliente.nombres}' creado/verificado.")

    # 5. Crear Caso en proceso[cite: 1]
    caso1, _ = Caso.objects.get_or_create(
        codigo='CAS-2026-001',
        defaults={
            'titulo': 'Demanda por Incumplimiento de Contrato',
            'descripcion': 'Juicio comercial por mora en pagos de inmueble.',
            'fecha_inicio': date(2026, 1, 15),
            'cliente': cliente,
            'estado': e_proceso
        }
    )
    caso1.abogados.set(usuarios_abogados)
    print(f"-> Caso '{caso1.codigo}' asignado a {len(usuarios_abogados)} abogados.")

    # 6. Crear Expedientes[cite: 1]
    Expediente.objects.get_or_create(
        numero='EXP-101-2026',
        defaults={
            'juzgado': '1° Juzgado Civil de Lima',
            'fecha_presentacion': date(2026, 1, 20),
            'caso': caso1
        }
    )
    Expediente.objects.get_or_create(
        numero='EXP-102-2026',
        defaults={
            'juzgado': '2° Sala Civil Superior',
            'fecha_presentacion': date(2026, 2, 5),
            'caso': caso1
        }
    )
    print("-> Expedientes creados.")

    # 7. Crear Pagos válidos[cite: 1]
    if not Pago.objects.filter(caso=caso1).exists():
        Pago.objects.create(caso=caso1, monto=1500.00, fecha=date(2026, 1, 25), descripcion='Adelanto de honorarios')
        Pago.objects.create(caso=caso1, monto=2000.00, fecha=date(2026, 2, 15), descripcion='Segundo pago')
        print("-> Pagos registrados correctamente.")

    # 8. Crear un Caso Archivado/Cancelado para probar el error de validación de pagos[cite: 1]
    caso_cancelado, _ = Caso.objects.get_or_create(
        codigo='CAS-2026-002',
        defaults={
            'titulo': 'Proceso de Arbitraje Cancelado',
            'descripcion': 'Arbitraje cerrado por acuerdo extrajudicial.',
            'fecha_inicio': date(2026, 2, 1),
            'cliente': cliente,
            'estado': e_cancelado
        }
    )
    print(f"-> Caso cancelado '{caso_cancelado.codigo}' creado para pruebas de error.")

    print("\n¡Proceso finalizado con éxito! Todos los datos fueron insertados.")

if __name__ == '__main__':
    poblar()