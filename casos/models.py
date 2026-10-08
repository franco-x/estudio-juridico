from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.core.exceptions import ValidationError


class PerfilAbogado(models.Model):
    """
    Relación OneToOne con User de Django para almacenar datos adicionales del abogado.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    numero_colegiatura = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=100)

    def __str__(self):
        nombre_completo = self.usuario.get_full_name() or self.usuario.username
        return f"{nombre_completo} (CAL: {self.numero_colegiatura})"


class Cliente(models.Model):
    """
    Modelo para gestionar clientes del estudio.
    """
    nombres = models.CharField(max_length=150)
    documento = models.CharField(max_length=20, unique=True)  # DNI o RUC único
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField()

    def __str__(self):
        return f"{self.nombres} ({self.documento})"


class EstadoCaso(models.Model):
    """
    Estados por los que pasa un caso.
    """
    nombre = models.CharField(max_length=50, unique=True)
    permite_pagos = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Caso(models.Model):
    """
    Modelo principal para representar el caso jurídico.
    """
    codigo = models.CharField(max_length=20, unique=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_inicio = models.DateField()
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='casos')
    estado = models.ForeignKey(EstadoCaso, on_delete=models.PROTECT, related_name='casos')
    abogados = models.ManyToManyField(User, related_name='casos_asignados')

    def total_pagado(self):
        """
        Devuelve la suma total de los pagos asociados usando el ORM (aggregate y Sum).
        Retorna 0.00 si no existen pagos registrados.
        """
        resultado = self.pagos.aggregate(total=Sum('monto'))['total']
        return resultado if resultado is not None else 0.00

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"


class Expediente(models.Model):
    """
    Expedientes judiciales asociados a un caso.
    """
    numero = models.CharField(max_length=50, unique=True)
    juzgado = models.CharField(max_length=150)
    fecha_presentacion = models.DateField()
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='expedientes')
    # Nuevo campo para subir archivos adjuntos
    documento = models.FileField(upload_to='expedientes/', blank=True, null=True)

    def __str__(self):
        return f"Exp. {self.numero} ({self.juzgado})"


class Pago(models.Model):
    """
    Pagos realizados para un caso específico.
    """
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    descripcion = models.TextField(blank=True, null=True)

    def clean(self):
        """
        Validación del modelo: impide guardar pagos si el estado del caso no lo permite.
        """
        super().clean()
        if self.caso_id and hasattr(self, 'caso') and self.caso.estado:
            if not self.caso.estado.permite_pagos:
                raise ValidationError(
                    f"No se pueden registrar pagos para el caso en estado '{self.caso.estado.nombre}'."
                )

    def __str__(self):
        return f"Pago S/. {self.monto} - Caso {self.caso.codigo}"