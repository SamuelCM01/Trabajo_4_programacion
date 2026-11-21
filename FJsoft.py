import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from abc import ABC, abstractmethod
from datetime import datetime


# ==========================================================
# 1. JERARQUÍA DE EXCEPCIONES PERSONALIZADAS
# ==========================================================
class ErrorSoftwareFJ(Exception):
    """Excepción base para todos los errores controlados de Software FJ."""
    pass


class DatoInvalidoError(ErrorSoftwareFJ):
    """Se lanza cuando un dato ingresado no cumple el formato o tipo esperado."""
    pass


class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """Se lanza al intentar reservar un servicio que ya está ocupado o inactivo."""
    pass


class ReservaError(ErrorSoftwareFJ):
    """Se lanza ante operaciones inválidas en el ciclo de vida de una reserva."""
    pass


class CalculoInconsistenteError(ErrorSoftwareFJ):
    """Se lanza cuando los parámetros de cálculo (impuestos/descuentos) son incoherentes."""
    pass


# ==========================================================
# 2. GESTOR DE LOGS (ARCHIVO + CONSOLA + INTERFAZ)
# ==========================================================
class GestorLogs:
    """Registra eventos y errores en archivo plano, consola real y consola visual."""

    def __init__(self, archivo="registro_software_fj.log"):
        self.archivo = archivo
        self.callback_visual = None  # Función opcional para enviar texto a la Consola Neón

    def conectar_consola_visual(self, callback):
        """Conecta la salida del log con la interfaz gráfica estilo CMD."""
        self.callback_visual = callback

    def registrar(self, nivel, mensaje, error_original=None):
        """Escribe el registro con fecha y hora sin detener el programa si falla el archivo."""
        marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{marca_tiempo}] [{nivel}] {mensaje}"
        if error_original is not None:
            linea += f" | Causa raíz: {type(error_original).__name__}: {error_original}"

        # 1. Salida en consola real de Python
        print(linea)

        # 2. Salida en archivo de logs (manejo seguro con try/except/finally)
        archivo_abierto = None
        try:
            archivo_abierto = open(self.archivo, "a", encoding="utf-8")
            archivo_abierto.write(linea + "\n")
        except OSError as e:
            print(f"[ALERTA DE ARCHIVO] No se pudo escribir en {self.archivo}: {e}")
        finally:
            if archivo_abierto is not None:
                archivo_abierto.close()

        # 3. Salida en la Consola Neón (si está abierta)
        if self.callback_visual:
            self.callback_visual(linea, nivel)


# ==========================================================
# 3. CLASE ABSTRACTA BASE: EntidadSistema
# ==========================================================
class EntidadSistema(ABC):
    """Molde abstracto para todas las entidades principales del sistema."""

    _contador_ids = 100

    def __init__(self):
        EntidadSistema._contador_ids += 1
        self._id = EntidadSistema._contador_ids
        self._fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def id(self):
        return self._id

    @property
    def fecha_creacion(self):
        return self._fecha_creacion

    @abstractmethod
    def validar(self):
        """Cada entidad debe implementar sus propias reglas de validación."""
        pass

    @abstractmethod
    def obtener_resumen(self):
        """Devuelve una cadena legible con el resumen de la entidad."""
        pass


# ==========================================================
# 4. CLASE CLIENTE (ENCAPSULACIÓN Y VALIDACIONES)
# ==========================================================
class Cliente(EntidadSistema):
    """Representa un cliente con datos personales encapsulados y validados."""

    def __init__(self, nombre, documento, correo, telefono):
        super().__init__()
        self.__nombre = None
        self.__documento = None
        self.__correo = None
        self.__telefono = None

        # Asignación mediante setters para activar las validaciones
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono
        self.validar()

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError("El nombre del cliente debe tener al menos 3 caracteres.")
        self.__nombre = valor.strip().title()

    @property
    def documento(self):
        return self.__documento

    @documento.setter
    def documento(self, valor):
        doc = str(valor).strip()
        if not doc.isdigit() or len(doc) < 5:
            raise DatoInvalidoError("El documento debe contener solo números (mínimo 5 dígitos).")
        self.__documento = doc

    @property
    def correo(self):
        return self.__correo

    @correo.setter
    def correo(self, valor):
        correo_str = str(valor).strip()
        if "@" not in correo_str or "." not in correo_str.split("@")[-1]:
            raise DatoInvalidoError(f"El correo '{correo_str}' no tiene un formato válido.")
        self.__correo = correo_str.lower()

    @property
    def telefono(self):
        return self.__telefono

    @telefono.setter
    def telefono(self, valor):
        tel = str(valor).strip()
        if not tel.isdigit() or len(tel) < 7:
            raise DatoInvalidoError("El teléfono debe contener solo dígitos (mínimo 7).")
        self.__telefono = tel

    def validar(self):
        if not all([self.__nombre, self.__documento, self.__correo, self.__telefono]):
            raise DatoInvalidoError("Todos los datos del cliente son obligatorios.")
        return True

    def obtener_resumen(self):
        return f"Cliente #{self.id} | {self.__nombre} (Doc: {self.__documento}) | {self.__correo}"


# ==========================================================
# 5. CLASE ABSTRACTA SERVICIO Y SUS 3 ESPECIALIZACIONES
# ==========================================================
class Servicio(EntidadSistema, ABC):
    """Clase abstracta base para los servicios ofrecidos por Software FJ."""

    def __init__(self, nombre, tarifa_base, disponible=True):
        super().__init__()
        self.nombre = str(nombre).strip()
        try:
            self.tarifa_base = float(tarifa_base)
        except (ValueError, TypeError) as e:
            # Encadenamiento de excepciones
            raise DatoInvalidoError("La tarifa base debe ser un valor numérico.") from e

        self.disponible = bool(disponible)
        self.validar()

    def validar(self):
        if not self.nombre:
            raise DatoInvalidoError("El nombre del servicio no puede estar vacío.")
        if self.tarifa_base <= 0:
            raise DatoInvalidoError("La tarifa base del servicio debe ser mayor a 0.")
        self.validar_parametros()
        return True

    @abstractmethod
    def validar_parametros(self):
        """Valida los parámetros específicos de cada tipo de servicio."""
        pass

    @abstractmethod
    def describir_servicio(self):
        """Devuelve una descripción detallada del servicio."""
        pass

    @abstractmethod
    def calcular_costo(self, duracion, impuesto=0.19, descuento=0.0, incluir_recargos=True):
        """Método polimórfico y sobrecargado mediante parámetros opcionales."""
        pass

    def _validar_calculo(self, duracion, impuesto, descuento):
        """Validación común para evitar cálculos inconsistentes."""
        try:
            dur = float(duracion)
            imp = float(impuesto)
            desc = float(descuento)
        except (ValueError, TypeError) as e:
            raise DatoInvalidoError("Duración, impuesto y descuento deben ser números.") from e

        if dur <= 0:
            raise DatoInvalidoError("La duración de la reserva debe ser mayor a 0.")
        if imp < 0 or imp > 0.5:
            raise CalculoInconsistenteError(f"Impuesto fuera de rango permitido (0% - 50%): {imp*100:.1f}%")
        if desc < 0 or desc >= 1.0:
            raise CalculoInconsistenteError(f"Descuento inconsistente (debe estar entre 0% y 99%): {desc*100:.1f}%")
        return dur, imp, desc

    def obtener_resumen(self):
        estado = "Disponible" if self.disponible else "Ocupado"
        return f"Servicio #{self.id} | {self.nombre} | ${self.tarifa_base:,.0f}/u | [{estado}]"


class ReservaSala(Servicio):
    """Servicio 1: Alquiler de salas de reuniones o capacitación."""

    def __init__(self, nombre, tarifa_base, capacidad, tiene_proyector=True):
        self.capacidad = capacidad
        self.tiene_proyector = bool(tiene_proyector)
        super().__init__(nombre, tarifa_base)

    def validar_parametros(self):
        try:
            self.capacidad = int(self.capacidad)
        except (ValueError, TypeError) as e:
            raise DatoInvalidoError("La capacidad de la sala debe ser un número entero.") from e
        if self.capacidad <= 0:
            raise DatoInvalidoError("La capacidad de la sala debe ser mayor a 0 personas.")

    def describir_servicio(self):
        proy = "con proyector 4K" if self.tiene_proyector else "sin proyector"
        return f"Sala '{self.nombre}' (Capacidad: {self.capacidad} personas, {proy})"

    def calcular_costo(self, duracion, impuesto=0.19, descuento=0.0, incluir_recargos=True):
        dur, imp, desc = self._validar_calculo(duracion, impuesto, descuento)
        subtotal = self.tarifa_base * dur
        if incluir_recargos and self.tiene_proyector:
            subtotal += 25000.0  # Recargo fijo por equipo audiovisual
        subtotal_con_desc = subtotal * (1 - desc)
        return subtotal_con_desc * (1 + imp)


class AlquilerEquipo(Servicio):
    """Servicio 2: Alquiler de equipos tecnológicos (portátiles, servidores, etc.)."""

    def __init__(self, nombre, tarifa_base, cantidad_unidades, deposito_seguro=50000.0):
        self.cantidad_unidades = cantidad_unidades
        self.deposito_seguro = deposito_seguro
        super().__init__(nombre, tarifa_base)

    def validar_parametros(self):
        try:
            self.cantidad_unidades = int(self.cantidad_unidades)
            self.deposito_seguro = float(self.deposito_seguro)
        except (ValueError, TypeError) as e:
            raise DatoInvalidoError("Cantidad de unidades y depósito deben ser numéricos.") from e
        if self.cantidad_unidades <= 0:
            raise DatoInvalidoError("La cantidad de equipos debe ser al menos 1.")
        if self.deposito_seguro < 0:
            raise DatoInvalidoError("El depósito de seguro no puede ser negativo.")

    def describir_servicio(self):
        return f"Alquiler '{self.nombre}' ({self.cantidad_unidades} uds. | Seguro: ${self.deposito_seguro:,.0f})"

    def calcular_costo(self, duracion, impuesto=0.19, descuento=0.0, incluir_recargos=True):
        dur, imp, desc = self._validar_calculo(duracion, impuesto, descuento)
        subtotal = self.tarifa_base * dur * self.cantidad_unidades
        if incluir_recargos:
            subtotal += self.deposito_seguro
        subtotal_con_desc = subtotal * (1 - desc)
        return subtotal_con_desc * (1 + imp)


class AsesoriaEspecializada(Servicio):
    """Servicio 3: Consultoría técnica especializada en software o arquitectura."""

    def __init__(self, nombre, tarifa_base, especialidad, es_urgente=False):
        self.especialidad = str(especialidad).strip()
        self.es_urgente = bool(es_urgente)
        super().__init__(nombre, tarifa_base)

    def validar_parametros(self):
        if len(self.especialidad) < 3:
            raise DatoInvalidoError("La especialidad técnica debe tener al menos 3 caracteres.")

    def describir_servicio(self):
        modalidad = "URGENTE (+30%)" if self.es_urgente else "Estándar"
        return f"Asesoría '{self.nombre}' en {self.especialidad} ({modalidad})"

    def calcular_costo(self, duracion, impuesto=0.19, descuento=0.0, incluir_recargos=True):
        dur, imp, desc = self._validar_calculo(duracion, impuesto, descuento)
        subtotal = self.tarifa_base * dur
        if incluir_recargos and self.es_urgente:
            subtotal *= 1.30  # Recargo del 30% por atención prioritaria
        subtotal_con_desc = subtotal * (1 - desc)
        return subtotal_con_desc * (1 + imp)


# ==========================================================
# 6. CLASE RESERVA (INTEGRADORA)
# ==========================================================
class Reserva(EntidadSistema):
    """Integra un Cliente y un Servicio con control de estado y cálculo de costos."""

    def __init__(self, cliente, servicio, duracion):
        super().__init__()
        self.cliente = cliente
        self.servicio = servicio
        try:
            self.duracion = float(duracion)
        except (ValueError, TypeError) as e:
            raise DatoInvalidoError("La duración de la reserva debe ser un número válido.") from e

        self.estado = "Pendiente"
        self.costo_final = 0.0
        self.validar()

    def validar(self):
        if not isinstance(self.cliente, Cliente):
            raise ReservaError("Se requiere una instancia válida de Cliente.")
        if not isinstance(self.servicio, Servicio):
            raise ReservaError("Se requiere una instancia válida de Servicio.")
        if self.duracion <= 0:
            raise DatoInvalidoError("La duración debe ser mayor a 0.")
        if not self.servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self.servicio.nombre}' no está disponible actualmente."
            )
        return True

    def confirmar(self, impuesto=0.19, descuento=0.0, incluir_recargos=True):
        """Confirma la reserva, calcula el costo y marca el servicio como ocupado."""
        if self.estado == "Confirmada":
            raise ReservaError(f"La reserva #{self.id} ya se encuentra confirmada.")
        if self.estado == "Cancelada":
            raise ReservaError(f"No se puede confirmar la reserva #{self.id} porque fue cancelada.")

        self.costo_final = self.servicio.calcular_costo(
            self.duracion,
            impuesto=impuesto,
            descuento=descuento,
            incluir_recargos=incluir_recargos
        )
        self.estado = "Confirmada"
        self.servicio.disponible = False
        return self.costo_final

    def cancelar(self):
        """Cancela la reserva y libera el servicio para futuros clientes."""
        if self.estado == "Cancelada":
            raise ReservaError(f"La reserva #{self.id} ya había sido cancelada previamente.")
        self.estado = "Cancelada"
        self.servicio.disponible = True

    def obtener_resumen(self):
        return (f"Reserva #{self.id} [{self.estado}] | {self.cliente.nombre} -> "
                f"{self.servicio.nombre} ({self.duracion}h) | Total: ${self.costo_final:,.2f}")


# ==========================================================
# 7. MOTOR CENTRAL DEL SISTEMA (SIN BASE DE DATOS)
# ==========================================================
class SistemaSoftwareFJ:
    """Controlador en memoria que gestiona clientes, servicios, reservas y pruebas."""

    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []
        self.logs = GestorLogs()

    def registrar_cliente(self, nombre, documento, correo, telefono):
        """Usa try/except/else para registrar clientes de forma segura."""
        try:
            cliente = Cliente(nombre, documento, correo, telefono)
        except ErrorSoftwareFJ as e:
            self.logs.registrar("ERROR", f"Fallo al registrar cliente '{nombre}': {e}", e.__cause__)
            return None
        else:
            self.clientes.append(cliente)
            self.logs.registrar("INFO", f"Registrado -> {cliente.obtener_resumen()}")
            return cliente

    def registrar_servicio(self, tipo_clase, *args, **kwargs):
        """Crea cualquier subclase de Servicio de forma polimórfica y controlada."""
        try:
            servicio = tipo_clase(*args, **kwargs)
        except ErrorSoftwareFJ as e:
            self.logs.registrar("ERROR", f"Fallo al crear servicio ({tipo_clase.__name__}): {e}", e.__cause__)
            return None
        else:
            self.servicios.append(servicio)
            self.logs.registrar("INFO", f"Servicio creado -> {servicio.describir_servicio()}")
            return servicio

    def procesar_reserva(self, cliente, servicio, duracion, impuesto=0.19, descuento=0.0, incluir_recargos=True):
        """Usa try/except/else/finally para procesar reservas de principio a fin."""
        reserva = None
        try:
            reserva = Reserva(cliente, servicio, duracion)
            reserva.confirmar(impuesto=impuesto, descuento=descuento, incluir_recargos=incluir_recargos)
        except ErrorSoftwareFJ as e:
            self.logs.registrar("ERROR", f"Reserva rechazada: {e}", e.__cause__)
            return None
        else:
            self.reservas.append(reserva)
            self.logs.registrar("INFO", f"Reserva confirmada -> {reserva.obtener_resumen()}")
            return reserva
        finally:
            estado_final = "EXITOSA" if reserva and reserva.estado == "Confirmada" else "CONTROLADA CON ERROR"
            self.logs.registrar("FINALLY", f"Ciclo de procesamiento de reserva cerrado ({estado_final}).")

    def cancelar_reserva(self, reserva):
        """Cancela una reserva existente validando su estado."""
        try:
            if not isinstance(reserva, Reserva):
                raise ReservaError("Objeto de reserva inválido para cancelación.")
            reserva.cancelar()
        except ErrorSoftwareFJ as e:
            self.logs.registrar("ERROR", f"Error al cancelar reserva: {e}")
            return False
        else:
            self.logs.registrar("INFO", f"Reserva #{reserva.id} cancelada. Servicio '{reserva.servicio.nombre}' liberado.")
            return True

    def ejecutar_simulacion_completa(self):
        """Simula 11 operaciones completas (válidas e inválidas) sin detener el sistema."""
        self.logs.registrar("INFO", "========================================================")
        self.logs.registrar("INFO", "INICIANDO BATERÍA DE PRUEBAS INTEGRALES - SOFTWARE FJ")
        self.logs.registrar("INFO", "========================================================")

        # Operación 1: Registro válido de Cliente 1
        c1 = self.registrar_cliente("Carlos Mendoza", "1090456789", "carlos.mendoza@correo.com", "3105551234")

        # Operación 2: Registro inválido de Cliente (correo sin '@' y documento corto)
        self.registrar_cliente("Ana Error", "123", "correo_invalido.com", "3001234567")

        # Operación 3: Registro válido de Cliente 2
        c2 = self.registrar_cliente("Laura Gómez", "1098765432", "laura.gomez@empresa.co", "3159998877")

        # Operación 4: Creación válida de 3 servicios especializados
        s1 = self.registrar_servicio(ReservaSala, "Sala Innovación A", 80000, 12, True)
        s2 = self.registrar_servicio(AlquilerEquipo, "Kit MacBook Pro M3", 45000, 3, 60000)
        s3 = self.registrar_servicio(AsesoriaEspecializada, "Arquitectura Cloud", 120000, "DevOps & AWS", True)

        # Operación 5: Creación inválida de servicio (tarifa en texto -> encadenamiento)
        self.registrar_servicio(ReservaSala, "Sala Defectuosa", "cien_mil", 10, False)

        # Operación 6: Creación inválida de servicio (capacidad negativa)
        self.registrar_servicio(ReservaSala, "Sala Imposible", 50000, -5, True)

        # Operación 7: Reserva exitosa con sobrecarga (IVA 19% + Descuento corporativo 10%)
        r1 = self.procesar_reserva(c1, s1, duracion=4, impuesto=0.19, descuento=0.10, incluir_recargos=True)

        # Operación 8: Reserva fallida por servicio no disponible (Sala ya ocupada por c1)
        self.procesar_reserva(c2, s1, duracion=2)

        # Operación 9: Reserva fallida por duración inválida (texto -> encadenamiento ValueError)
        self.procesar_reserva(c2, s2, duracion="tres_horas")

        # Operación 10: Cálculo inconsistente (descuento del 150%)
        self.procesar_reserva(c2, s3, duracion=3, impuesto=0.19, descuento=1.50)

        # Operación 11: Reserva exitosa de Asesoría + Cancelación exitosa + Re-cancelación fallida
        r2 = self.procesar_reserva(c2, s3, duracion=2, impuesto=0.19, descuento=0.0, incluir_recargos=True)
        self.cancelar_reserva(r1)
        self.cancelar_reserva(r1)  # Intento duplicado -> captura ReservaError

        self.logs.registrar("INFO", "========================================================")
        self.logs.registrar(
            "INFO",
            f"RESUMEN EN MEMORIA -> Clientes: {len(self.clientes)} | "
            f"Servicios: {len(self.servicios)} | Reservas: {len(self.reservas)}"
        )
        self.logs.registrar("INFO", f"Logs guardados correctamente en: {self.logs.archivo}")
        self.logs.registrar("INFO", "SIMULACIÓN FINALIZADA SIN INTERRUPCIONES.")


# ==========================================================
# 8. INTERFAZ 2: CONSOLA NEÓN DE PRUEBAS (ESTILO CMD)
# ==========================================================
class VentanaConsolaNeon(tk.Toplevel):
    """Ventana secundaria con estética de terminal oscura y adornos verde neón."""

    def __init__(self, parent, sistema):
        super().__init__(parent)
        self.sistema = sistema
        self.title("Software FJ :: Consola de Pruebas del Sistema")
        self.geometry("820x560")
        self.configure(bg="#050505")
        self.resizable(False, False)

        # Encabezado neón
        lbl_titulo = tk.Label(
            self,
            text="[ SOFTWARE FJ :: TERMINAL DE DIAGNÓSTICO Y PRUEBAS ]",
            bg="#050505",
            fg="#39FF14",
            font=("Consolas", 13, "bold")
        )
        lbl_titulo.pack(pady=(12, 5))

        # Canvas decorativo con rayas verde neón en las esquinas
        self.canvas = tk.Canvas(self, width=780, height=430, bg="#050505", highlightthickness=0)
        self.canvas.pack(pady=5)
        self._dibujar_marco_neon()

        # Área de texto estilo CMD dentro del Canvas
        self.txt_consola = scrolledtext.ScrolledText(
            self.canvas,
            bg="#0A0A0A",
            fg="#39FF14",
            insertbackground="#39FF14",
            font=("Consolas", 9),
            relief="flat",
            borderwidth=0,
            state="disabled"
        )
        self.canvas.create_window(390, 215, window=self.txt_consola, width=730, height=385)

        # Etiquetas de color para diferenciar niveles de log
        self.txt_consola.tag_config("INFO", foreground="#39FF14")     # Verde neón
        self.txt_consola.tag_config("ERROR", foreground="#FF4C4C")    # Rojo suave
        self.txt_consola.tag_config("FINALLY", foreground="#00E5FF")  # Cian neón

        # Botonera inferior
        frame_btns = tk.Frame(self, bg="#050505")
        frame_btns.pack(pady=10)

        estilo_btn = {
            "bg": "#0D0D0D",
            "fg": "#39FF14",
            "activebackground": "#39FF14",
            "activeforeground": "#050505",
            "font": ("Consolas", 10, "bold"),
            "relief": "solid",
            "bd": 1,
            "width": 18,
            "cursor": "hand2"
        }

        tk.Button(frame_btns, text="> EJECUTAR PRUEBAS", command=self.correr_pruebas, **estilo_btn).pack(side="left", padx=8)
        tk.Button(frame_btns, text="> LIMPIAR CONSOLA", command=self.limpiar, **estilo_btn).pack(side="left", padx=8)
        tk.Button(frame_btns, text="> VOLVER AL MENÚ", command=self.cerrar, **estilo_btn).pack(side="left", padx=8)

        # Conectar logs a esta consola
        self.sistema.logs.conectar_consola_visual(self.escribir_linea)
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

        # Mensaje inicial
        self.escribir_linea("Sistema listo. Presione '> EJECUTAR PRUEBAS' para iniciar la simulación...", "INFO")

    def _dibujar_marco_neon(self):
        """Dibuja escuadras y líneas verde neón en las 4 esquinas para delimitar la terminal."""
        c = "#39FF14"
        w, h = 780, 430
        m = 12   # Margen exterior
        l = 45   # Longitud de las rayas de esquina

        # Esquina superior izquierda
        self.canvas.create_line(m, m, m + l, m, fill=c, width=2)
        self.canvas.create_line(m, m, m, m + l, fill=c, width=2)
        self.canvas.create_line(m + 6, m + 6, m + 25, m + 6, fill=c, width=1)

        # Esquina superior derecha
        self.canvas.create_line(w - m, m, w - m - l, m, fill=c, width=2)
        self.canvas.create_line(w - m, m, w - m, m + l, fill=c, width=2)
        self.canvas.create_line(w - m - 6, m + 6, w - m - 25, m + 6, fill=c, width=1)

        # Esquina inferior izquierda
        self.canvas.create_line(m, h - m, m + l, h - m, fill=c, width=2)
        self.canvas.create_line(m, h - m, m, h - m - l, fill=c, width=2)
        self.canvas.create_line(m + 6, h - m - 6, m + 25, h - m - 6, fill=c, width=1)

        # Esquina inferior derecha
        self.canvas.create_line(w - m, h - m, w - m - l, h - m, fill=c, width=2)
        self.canvas.create_line(w - m, h - m, w - m, h - m - l, fill=c, width=2)
        self.canvas.create_line(w - m - 6, h - m - 6, w - m - 25, h - m - 6, fill=c, width=1)

    def escribir_linea(self, texto, nivel="INFO"):
        self.txt_consola.config(state="normal")
        self.txt_consola.insert(tk.END, texto + "\n", nivel)
        self.txt_consola.see(tk.END)
        self.txt_consola.config(state="disabled")
        self.update_idletasks()

    def correr_pruebas(self):
        self.sistema.ejecutar_simulacion_completa()

    def limpiar(self):
        self.txt_consola.config(state="normal")
        self.txt_consola.delete("1.0", tk.END)
        self.txt_consola.config(state="disabled")

    def cerrar(self):
        self.sistema.logs.conectar_consola_visual(None)
        self.destroy()


# ==========================================================
# 9. INTERFAZ INTERACTIVA DE GESTIÓN ("INGRESAR")
# ==========================================================
class VentanaGestion(tk.Toplevel):
    """Panel interactivo sencillo para operar el sistema manualmente."""

    def __init__(self, parent, sistema):
        super().__init__(parent)
        self.sistema = sistema
        self.title("Software FJ - Panel de Gestión")
        self.geometry("620x460")
        self.resizable(False, False)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña 1: Clientes
        tab_cli = tk.Frame(notebook, padx=10, pady=10)
        notebook.add(tab_cli, text="Clientes")

        tk.Label(tab_cli, text="Nombre:").grid(row=0, column=0, sticky="w", pady=3)
        self.e_nom = tk.Entry(tab_cli, width=30)
        self.e_nom.grid(row=0, column=1, pady=3)

        tk.Label(tab_cli, text="Documento:").grid(row=1, column=0, sticky="w", pady=3)
        self.e_doc = tk.Entry(tab_cli, width=30)
        self.e_doc.grid(row=1, column=1, pady=3)

        tk.Label(tab_cli, text="Correo:").grid(row=2, column=0, sticky="w", pady=3)
        self.e_cor = tk.Entry(tab_cli, width=30)
        self.e_cor.grid(row=2, column=1, pady=3)

        tk.Label(tab_cli, text="Teléfono:").grid(row=3, column=0, sticky="w", pady=3)
        self.e_tel = tk.Entry(tab_cli, width=30)
        self.e_tel.grid(row=3, column=1, pady=3)

        tk.Button(tab_cli, text="Registrar Cliente", command=self.crear_cliente, bg="#4CAF50", fg="white").grid(
            row=4, column=0, columnspan=2, pady=8
        )

        self.lst_clientes = tk.Listbox(tab_cli, width=75, height=10)
        self.lst_clientes.grid(row=5, column=0, columnspan=2, pady=5)

        # Pestaña 2: Servicios y Reservas en Memoria
        tab_res = tk.Frame(notebook, padx=10, pady=10)
        notebook.add(tab_res, text="Resumen en Memoria")

        self.txt_resumen = scrolledtext.ScrolledText(tab_res, width=70, height=18, state="disabled")
        self.txt_resumen.pack(fill="both", expand=True, pady=5)

        tk.Button(tab_res, text="Actualizar Vista", command=self.refrescar_datos, bg="#2196F3", fg="white").pack(pady=5)

        self.refrescar_datos()

    def crear_cliente(self):
        c = self.sistema.registrar_cliente(
            self.e_nom.get(), self.e_doc.get(), self.e_cor.get(), self.e_tel.get()
        )
        if c:
            messagebox.showinfo("Éxito", f"Cliente registrado:\n{c.obtener_resumen()}")
            for e in (self.e_nom, self.e_doc, self.e_cor, self.e_tel):
                e.delete(0, tk.END)
            self.refrescar_datos()
        else:
            messagebox.showerror("Error de Validación", "Datos inválidos. Revise el archivo de logs o la consola.")

    def refrescar_datos(self):
        self.lst_clientes.delete(0, tk.END)
        for c in self.sistema.clientes:
            self.lst_clientes.insert(tk.END, c.obtener_resumen())

        self.txt_resumen.config(state="normal")
        self.txt_resumen.delete("1.0", tk.END)
        self.txt_resumen.insert(tk.END, "--- SERVICIOS REGISTRADOS ---\n")
        for s in self.sistema.servicios:
            self.txt_resumen.insert(tk.END, f"• {s.obtener_resumen()} -> {s.describir_servicio()}\n")
        self.txt_resumen.insert(tk.END, "\n--- RESERVAS REGISTRADAS ---\n")
        for r in self.sistema.reservas:
            self.txt_resumen.insert(tk.END, f"• {r.obtener_resumen()}\n")
        self.txt_resumen.config(state="disabled")


# ==========================================================
# 10. INTERFAZ 1: MENÚ PRINCIPAL (TKINTER REGULAR)
# ==========================================================
class AppSoftwareFJ:
    """Ventana principal de bienvenida con acceso a Gestión y Prueba de Sistema."""

    def __init__(self):
        self.sistema = SistemaSoftwareFJ()
        self.root = tk.Tk()
        self.root.title("Software FJ - Sistema de Gestión")
        self.root.geometry("360x300")
        self.root.resizable(False, False)

        # Título principal
        tk.Label(
            self.root,
            text="SOFTWARE FJ",
            font=("Arial", 18, "bold"),
            fg="#1E3A5F"
        ).pack(pady=(25, 5))

        tk.Label(
            self.root,
            text="Gestión de Clientes, Servicios y Reservas",
            font=("Arial", 9, "italic"),
            fg="#555555"
        ).pack(pady=(0, 20))

        # Botones verticales solicitados
        tk.Button(
            self.root,
            text="Ingresar",
            command=self.abrir_gestion,
            width=22,
            height=2,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(pady=6)

        tk.Button(
            self.root,
            text="Prueba de Sistema",
            command=self.abrir_prueba_sistema,
            width=22,
            height=2,
            bg="#111111",
            fg="#39FF14",
            font=("Consolas", 10, "bold")
        ).pack(pady=6)

        tk.Button(
            self.root,
            text="Salir",
            command=self.salir,
            width=22,
            height=2,
            bg="#D32F2F",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(pady=6)

    def abrir_gestion(self):
        VentanaGestion(self.root, self.sistema)

    def abrir_prueba_sistema(self):
        VentanaConsolaNeon(self.root, self.sistema)

    def salir(self):
        self.sistema.logs.registrar("INFO", "Aplicación cerrada por el usuario.")
        self.root.destroy()

    def iniciar(self):
        self.root.mainloop()


# ==========================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# ==========================================================
if __name__ == "__main__":
    app = AppSoftwareFJ()
    app.iniciar()