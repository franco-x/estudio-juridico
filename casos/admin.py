from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilAbogado, Cliente, EstadoCaso, Caso, Expediente, Pago


# 1. Inline de PerfilAbogado para el mantenedor de usuarios (StackedInline)
class PerfilAbogadoInline(admin.StackedInline):
    model = PerfilAbogado
    can_delete = False
    verbose_name_plural = 'Perfil de Abogado'


# Definición del nuevo UserAdmin que incluye PerfilAbogado
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilAbogadoInline,)


# Re-registrar el modelo User con la nueva configuración
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# 2. Inlines para el mantenedor de Casos (TabularInline)
class ExpedienteInline(admin.TabularInline):
    model = Expediente
    extra = 1


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 1


# 3. Mantenedor de Cliente
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'documento', 'telefono', 'correo')
    search_fields = ('nombres', 'documento')
    list_filter = ('nombres',)


# 4. Mantenedor de EstadoCaso
@admin.register(EstadoCaso)
class EstadoCasoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'permite_pagos')
    search_fields = ('nombre',)
    list_filter = ('permite_pagos',)


# 5. Mantenedor de Expediente
@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('numero', 'juzgado', 'fecha_presentacion', 'caso')
    search_fields = ('numero', 'juzgado')
    list_filter = ('fecha_presentacion', 'juzgado')


# 6. Mantenedor de Caso con Inlines y filter_horizontal
@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'titulo', 'cliente', 'estado', 'obtener_total_pagado')
    search_fields = ('codigo', 'titulo', 'cliente__nombres', 'cliente__documento')
    list_filter = ('estado', 'fecha_inicio')
    filter_horizontal = ('abogados',)  # Asignación horizontal de abogados
    inlines = [ExpedienteInline, PagoInline]  # Inlines de expedientes y pagos

    def obtener_total_pagado(self, obj):
        """Muestra el total pagado formateado en la lista de casos."""
        return f"S/. {obj.total_pagado():.2f}"
    
    obtener_total_pagado.short_description = 'Total Pagado'