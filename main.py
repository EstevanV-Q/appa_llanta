from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from datetime import datetime
import sqlite3
import os
import traceback
from fpdf import FPDF, HTMLMixin
from datetime import datetime
import subprocess
import platform

# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
# from reportlab.lib import colors
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.graphics.shapes import Drawing
# from reportlab.graphics.charts.barcharts import VerticalBarChart


from kivy.config import Config
from kivy.utils import platform

# Configurar la aplicación para móviles
if platform == 'android' or platform == 'ios':
    Config.set('graphics', 'width', '0')
    Config.set('graphics', 'height', '0')
    Config.set('graphics', 'resizable', '0')
else:
    Window.size = (400, 600)  # Tamaño por defecto para desktop

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        try:
            self.conn = sqlite3.connect('tirestore.db')
            self.c = self.conn.cursor()
            self.create_tables()
        except Exception as e:
            self.log_error(f"Error de base de datos: {str(e)}")

    def create_tables(self):
        try:
            self.c.executescript('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    size TEXT NOT NULL,
                    type TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL,
                    total REAL NOT NULL,
                    customer_id INTEGER,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                );

                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    address TEXT
                );

                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY,
                    sale_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER,
                    price REAL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                );
            ''')
            self.conn.commit()
        except Exception as e:
            self.log_error(f"Error creando tablas: {str(e)}")

    def add_product(self, name, brand, size, type_, price, stock):
        try:
            self.c.execute('''
                INSERT INTO products (name, brand, size, type, price, stock)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, brand, size, type_, price, stock))
            self.conn.commit()
            self.log_action("Producto añadido correctamente")
            return True
        except Exception as e:
            self.log_error(f"Error añadiendo producto: {str(e)}")
            return False

    def get_products(self):
        try:
            self.c.execute('SELECT * FROM products')
            self.log_action("Productos obtenidos correctamente")
            return self.c.fetchall()
        except Exception as e:
            self.log_error(f"Error obteniendo productos: {str(e)}")
            return []

    def update_stock(self, product_id, quantity):
        try:
            self.c.execute('''
                UPDATE products
                SET stock = stock + ?
                WHERE id = ?
            ''', (quantity, product_id))
            self.conn.commit()
            self.log_action(f"Stock actualizado para el producto ID: {product_id}")
            return True
        except Exception as e:
            self.log_error(f"Error actualizando stock: {str(e)}")
            return False

    def add_customer(self, name, phone, email, address):
        try:
            self.c.execute('''
                INSERT INTO customers (name, phone, email, address)
                VALUES (?, ?, ?, ?)
            ''', (name, phone, email, address))
            self.conn.commit()
            self.log_action("Cliente añadido correctamente")
            return True
        except Exception as e:
            self.log_error(f"Error añadiendo cliente: {str(e)}")
            return False

    def get_customers(self):
        try:
            self.c.execute('SELECT * FROM customers')
            self.log_action("Clientes obtenidos correctamente")
            return self.c.fetchall()
        except Exception as e:
            self.log_error(f"Error obteniendo clientes: {str(e)}")
            return []

    def add_sale(self, total, customer_id=None):
        try:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.c.execute('''
                INSERT INTO sales (date, total, customer_id)
                VALUES (?, ?, ?)
            ''', (date, total, customer_id))
            self.conn.commit()
            self.log_action("Venta añadida correctamente")
            return self.c.lastrowid
        except Exception as e:
            self.log_error(f"Error añadiendo venta: {str(e)}")
            return None

    def add_sale_item(self, sale_id, product_id, quantity, price):
        try:
            self.c.execute('''
                INSERT INTO sale_items (sale_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (sale_id, product_id, quantity, price))
            self.conn.commit()
            self.log_action(f"Ítem de venta añadido correctamente para la venta ID: {sale_id}")
            return True
        except Exception as e:
            self.log_error(f"Error añadiendo ítem de venta: {str(e)}")
            return False

    def get_sales_report(self):
        try:
            self.c.execute('''
                SELECT s.id, s.date, s.total, c.name, GROUP_CONCAT(p.name, ', ')
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                LEFT JOIN sale_items si ON s.id = si.sale_id
                LEFT JOIN products p ON si.product_id = p.id
                GROUP BY s.id
            ''')
            self.log_action("Reporte de ventas obtenido correctamente")
            return self.c.fetchall()
        except Exception as e:
            self.log_error(f"Error obteniendo reporte de ventas: {str(e)}")
            return []

    def log_error(self, message):
        try:
            with open('error_log.txt', 'a') as file:
                file.write(f"{datetime.now()}: ERROR - {message}\n")
                file.write(f"Traceback: {traceback.format_exc()}\n")
        except Exception as e:
            print(f"Error al guardar el log: {str(e)}")

    def log_action(self, message):
        try:
            with open('action_log.txt', 'a') as file:
                file.write(f"{datetime.now()}: {message}\n")
        except Exception as e:
            print(f"Error al guardar el log de acción: {str(e)}")

class MessagePopup(BoxLayout):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.size_hint = (None, None)
        self.size = (300, 200)
        self.pos_hint = {'center_x': .5, 'center_y': .5}

        # Accede al Label usando ids
        self.ids.message_label.text = message

        btn = Button(text='Cerrar', size_hint_y=None, height=50)
        btn.bind(on_release=self.dismiss)
        self.add_widget(btn)

        # Asegúrate de que el popup se añade a un contenedor antes de programar su eliminación
        Clock.schedule_once(lambda dt: self.dismiss(), 5)   # Cerrar automáticamente después de 5 segundos

    def dismiss(self, *args):
        if self.parent:
            self.parent.remove_widget(self)


class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.update_layout)

    def update_layout(self, instance, value):
        # Ajustar el layout cuando cambia el tamaño de la pantalla
        pass

    def show_message(self, message):
        popup = MessagePopup(message)
        self.add_widget(popup)

class LoginScreen(BaseScreen):
    def verify_login(self):
        try:
            if self.ids.username.text.strip() and self.ids.password.text.strip():
                # Aquí deberías implementar una verificación real
                if self.ids.username.text == 'admin' and self.ids.password.text == 'admin':
                    self.manager.transition = SlideTransition(direction='left')
                    self.manager.current = 'main'
                else:
                    self.show_message('Usuario o contraseña incorrectos')
            else:
                self.show_message('Por favor complete todos los campos')
        except Exception as e:
            self.show_message(f'Error en el login: {str(e)}')

class MainScreen(BaseScreen):
    def switch_screen(self, screen_name):
        try:
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = screen_name
        except Exception as e:
            self.show_message(f'Error cambiando de pantalla: {str(e)}')

    def logout(self):
        try:
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = 'login'
        except Exception as e:
            self.show_message(f'Error en logout: {str(e)}')

class ProductScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()

    def validate_inputs(self):
        try:
            if not all(input_widget.text.strip() for input_widget in [self.ids.name, self.ids.brand, self.ids.size, self.ids.price, self.ids.stock]):
                self.show_message('Por favor complete todos los campos')
                return False

            try:
                price = float(self.ids.price.text)
                stock = int(self.ids.stock.text)
                if price <= 0 or stock < 0:
                    self.show_message('El precio debe ser mayor a 0 y el stock no puede ser negativo')
                    return False
            except ValueError:
                self.show_message('Precio y stock deben ser números válidos')
                return False

            return True
        except Exception as e:
            self.show_message(f'Error en validación: {str(e)}')
            return False

    def save_product(self):
        try:
            if not self.validate_inputs():
                return

            success = self.db.add_product(
                self.ids.name.text,
                self.ids.brand.text,
                self.ids.size.text,
                self.ids.type.text,
                float(self.ids.price.text),
                int(self.ids.stock.text)
            )

            if success:
                self.show_message('Producto guardado correctamente')
                self.clear_inputs()
            else:
                self.show_message('Error al guardar el producto')

        except Exception as e:
            self.show_message(f'Error guardando producto: {str(e)}')

    def clear_inputs(self):
        for input_widget in [self.ids.name, self.ids.brand, self.ids.size, self.ids.price, self.ids.stock]:
            input_widget.text = ''
        self.ids.type.text = self.ids.type.values[0]

    def generate_report(self, report_type):
        try:
            reports_screen = self.manager.get_screen('reports')
            reports_screen.generate_report(report_type)
        except Exception as e:
            self.show_message(f'Error generando reporte: {str(e)}')

    def go_back(self):
        try:
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = 'main'
        except Exception as e:
            self.show_message(f'Error volviendo al menú principal: {str(e)}')

class SalesScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        Clock.schedule_once(lambda dt: self.setup_spinners())

    def setup_spinners(self, *args):
        try:
            # Actualizar el spinner de productos
            products = self.get_product_names()
            self.ids.product_spinner.values = products

            # Actualizar el spinner de clientes
            customers = self.get_customer_names()
            self.ids.customer_spinner.values = customers
        except Exception as e:
            self.show_message(f"Error configurando spinners: {str(e)}")

    def get_product_names(self):
        try:
            products = self.db.get_products()
            return [f"{p[1]} - {p[2]} ({p[3]})" for p in products]
        except Exception as e:
            self.show_message(f"Error cargando productos: {str(e)}")
            return []

    def get_customer_names(self):
        try:
            customers = self.db.get_customers()
            return [f"{c[1]}" for c in customers]
        except Exception as e:
            self.show_message(f"Error cargando clientes: {str(e)}")
            return []

    def register_sale(self):
        try:
            if not self.validate_sale():
                return

            product_name = self.ids.product_spinner.text.split(' - ')[0]
            quantity = int(self.ids.quantity_input.text)
            customer_name = self.ids.customer_spinner.text

            # Obtener IDs de producto y cliente
            product_id = self.get_product_id(product_name)
            customer_id = self.get_customer_id(customer_name)

            if product_id is None or customer_id is None:
                self.show_message("Error obteniendo IDs de producto o cliente")
                return

            # Obtener precio del producto
            price = self.get_product_price(product_id)
            if price is None:
                self.show_message("Error obteniendo precio del producto")
                return

            # Calcular total
            total = price * quantity

            # Registrar venta
            sale_id = self.db.add_sale(total, customer_id)
            if sale_id is None:
                self.show_message("Error registrando venta")
                return

            # Registrar ítem de venta
            success = self.db.add_sale_item(sale_id, product_id, quantity, price)
            if not success:
                self.show_message("Error registrando ítem de venta")
                return

            # Actualizar stock
            self.db.update_stock(product_id, -quantity)

            self.show_message("Venta registrada correctamente")
            self.clear_inputs()

        except Exception as e:
            self.show_message(f"Error registrando venta: {str(e)}")

    def validate_sale(self):
        try:
            if self.ids.product_spinner.text == 'Seleccionar Producto':
                self.show_message("Por favor seleccione un producto")
                return False

            if not self.ids.quantity_input.text:
                self.show_message("Por favor ingrese una cantidad")
                return False

            try:
                quantity = int(self.ids.quantity_input.text)
                if quantity <= 0:
                    self.show_message("La cantidad debe ser mayor que cero")
                    return False
            except ValueError:
                self.show_message("La cantidad debe ser un número entero")
                return False

            if self.ids.customer_spinner.text == 'Seleccionar Cliente':
                self.show_message("Por favor seleccione un cliente")
                return False

            # Verificar stock disponible
            product_name = self.ids.product_spinner.text.split(' - ')[0]
            product_id = self.get_product_id(product_name)
            products = self.db.get_products()

            for product in products:
                if product[0] == product_id:
                    if product[6] < quantity:  # product[6] es el stock
                        self.show_message(f"Stock insuficiente. Disponible: {product[6]}")
                        return False
                    break

            return True

        except Exception as e:
            self.show_message(f"Error en validación: {str(e)}")
            return False

    def clear_inputs(self):
        self.ids.product_spinner.text = 'Seleccionar Producto'
        self.ids.quantity_input.text = ''
        self.ids.customer_spinner.text = 'Seleccionar Cliente'

    def get_product_id(self, product_name):
        try:
            products = self.db.get_products()
            for product in products:
                if product[1] == product_name:
                    return product[0]
            return None
        except Exception as e:
            self.show_message(f"Error obteniendo ID de producto: {str(e)}")
            return None

    def get_customer_id(self, customer_name):
        try:
            customers = self.db.get_customers()
            for customer in customers:
                if customer[1] == customer_name:
                    return customer[0]
            return None
        except Exception as e:
            self.show_message(f"Error obteniendo ID de cliente: {str(e)}")
            return None

    def get_product_price(self, product_id):
        try:
            products = self.db.get_products()
            for product in products:
                if product[0] == product_id:
                    return product[5]
            return None
        except Exception as e:
            self.show_message(f"Error obteniendo precio de producto: {str(e)}")
            return None

    def generate_report(self, report_type):
        try:
            reports_screen = self.manager.get_screen('reports')
            reports_screen.generate_report(report_type)
        except Exception as e:
            self.show_message(f'Error generando reporte: {str(e)}')

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'main'

class CustomersScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()

    def add_customer(self):
        try:
            if not self.validate_customer():
                return

            # Limpiar espacios en blanco extras
            name = self.ids.name_input.text.strip()
            phone = self.ids.phone_input.text.strip()
            email = self.ids.email_input.text.strip()
            address = self.ids.address_input.text.strip()

            success = self.db.add_customer(
                name,
                phone,
                email,
                address
            )

            if success:
                self.show_message("Cliente añadido correctamente")
                self.clear_inputs()
            else:
                self.show_message("Error añadiendo cliente")

        except Exception as e:
            self.show_message(f"Error añadiendo cliente: {str(e)}")

    def validate_customer(self):
        try:
            if not self.ids.name_input.text.strip():
                self.show_message("Por favor ingrese el nombre del cliente")
                return False

            # Validar formato de teléfono (opcional)
            phone = self.ids.phone_input.text.strip()
            if phone and not phone.replace('+', '').replace(' ', '').replace('-', '').isdigit():
                self.show_message("El teléfono solo debe contener números, +, - y espacios")
                return False

            # Validar formato de email (opcional)
            email = self.ids.email_input.text.strip()
            if email and '@' not in email:
                self.show_message("Por favor ingrese un email válido")
                return False

            return True
        except Exception as e:
            self.show_message(f"Error en validación: {str(e)}")
            return False

    def clear_inputs(self):
        self.ids.name_input.text = ''
        self.ids.phone_input.text = ''
        self.ids.email_input.text = ''
        self.ids.address_input.text = ''

    def generate_report(self, report_type):
        try:
            reports_screen = self.manager.get_screen('reports')
            reports_screen.generate_report(report_type)
        except Exception as e:
            self.show_message(f'Error generando reporte: {str(e)}')

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'main'


# Modifica la función generate_business_report
class ProfessionalPDF(FPDF):
    def __init__(self, report_title="Reporte TireStore"):
        super().__init__()
        self.report_title = report_title
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_margins(20, 20, 20)
        
    def header(self):
        # Logo
        if os.path.exists('logo.png'):
            self.image('logo.png', 10, 8, 33)
        
        # Title
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        self.cell(0, 10, datetime.now().strftime("%d/%m/%Y %H:%M"), 0, 0, 'R')

def generate_professional_report(data, config):
    try:
        pdf = ProfessionalPDF(config['title'])
        pdf.set_font('Helvetica', 'B', 16)
        
        # Subtítulo
        if 'subtitle' in config:
            pdf.set_font('Helvetica', 'I', 12)
            pdf.cell(0, 10, config['subtitle'], 0, 1, 'C')
            pdf.ln(5)

        # Introducción
        if 'introduction' in config:
            pdf.set_font('Helvetica', '', 11)
            pdf.multi_cell(0, 10, config['introduction'])
            pdf.ln(10)

        # Contenido del reporte
        pdf.set_font('Helvetica', '', 10)
        
        if 'products' in data:
            # Tabla de productos
            headers = ['ID', 'Producto', 'Marca', 'Tamaño', 'Tipo', 'Precio', 'Stock']
            products = data['products']
            
            # Calcular anchos de columna
            col_widths = [20, 40, 30, 25, 25, 25, 20]
            
            # Encabezados
            pdf.set_font('Helvetica', 'B', 10)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1)
            pdf.ln()
            
            # Datos
            pdf.set_font('Helvetica', '', 10)
            for product in products:
                pdf.cell(col_widths[0], 10, str(product['ID']), 1)
                pdf.cell(col_widths[1], 10, product['Producto'], 1)
                pdf.cell(col_widths[2], 10, product['Marca'], 1)
                pdf.cell(col_widths[3], 10, product['Tamaño'], 1)
                pdf.cell(col_widths[4], 10, product['Tipo'], 1)
                # Convertir el símbolo de colón a un símbolo compatible
                precio = product['Precio'].replace('₡', 'CRC ')
                pdf.cell(col_widths[5], 10, precio, 1)
                pdf.cell(col_widths[6], 10, str(product['Stock']), 1)
                pdf.ln()

        elif 'sales' in data:
            # Tabla de ventas
            headers = ['ID', 'Fecha', 'Total', 'Cliente', 'Productos']
            sales = data['sales']
            
            # Calcular anchos de columna
            col_widths = [20, 35, 30, 40, 60]
            
            # Encabezados
            pdf.set_font('Helvetica', 'B', 10)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1)
            pdf.ln()
            
            # Datos
            pdf.set_font('Helvetica', '', 10)
            for sale in sales:
                pdf.cell(col_widths[0], 10, str(sale['ID']), 1)
                pdf.cell(col_widths[1], 10, sale['Fecha'], 1)
                # Convertir el símbolo de colón a un símbolo compatible
                total = sale['Total'].replace('₡', 'CRC ')
                pdf.cell(col_widths[2], 10, total, 1)
                pdf.cell(col_widths[3], 10, sale['Cliente'], 1)
                pdf.cell(col_widths[4], 10, sale['Productos'], 1)
                pdf.ln()

        elif 'customers' in data:
            # Tabla de clientes
            headers = ['ID', 'Nombre', 'Teléfono', 'Email', 'Dirección']
            customers = data['customers']
            
            # Calcular anchos de columna
            col_widths = [20, 40, 30, 50, 45]
            
            # Encabezados
            pdf.set_font('Helvetica', 'B', 10)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1)
            pdf.ln()
            
            # Datos
            pdf.set_font('Helvetica', '', 10)
            for customer in customers:
                pdf.cell(col_widths[0], 10, str(customer['ID']), 1)
                pdf.cell(col_widths[1], 10, customer['Nombre'], 1)
                pdf.cell(col_widths[2], 10, customer['Teléfono'], 1)
                pdf.cell(col_widths[3], 10, customer['Email'], 1)
                pdf.cell(col_widths[4], 10, customer['Dirección'], 1)
                pdf.ln()

        # Guardar el PDF
        pdf.output(config['output_file'])
        return True
    except Exception as e:
        print(f"Error generando reporte PDF: {str(e)}")
        traceback.print_exc()
        return False

class ReportsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.report_types = {
            'inventory': self.generate_inventory_report,
            'sales': self.generate_sales_report,
            'customers': self.generate_customers_report,
            'full': self.generate_full_report
        }

    def generate_report(self, report_type):
        if report_type in self.report_types:
            self.report_types[report_type]()
        else:
            self.show_message("Tipo de reporte no válido")

    def generate_inventory_report(self):
        try:
            products = self.db.get_products()
            if not products:
                self.show_message("¡Inventario vacío! No hay productos registrados")
                return
            config = {
                'title': 'Reporte de Inventario',
                'subtitle': 'Estado Actual del Stock',
                'logo_path': './logo.png' if os.path.exists('./logo.png') else None,
                'output_file': 'inventory_report.pdf',
                'introduction': 'Resumen detallado del inventario actual de productos con información de stock y precios.',
                'author': 'Sistema de Gestión TireStore'
            }
            formatted_products = [{
                "ID": p[0],
                "Producto": p[1],
                "Marca": p[2],
                "Tamaño": p[3],
                "Tipo": p[4],
                "Precio": f"₡{p[5]:,.2f}",
                "Stock": p[6]
            } for p in products]
            if generate_professional_report({'products': formatted_products}, config):
                self.show_message("Reporte de inventario generado: inventory_report.pdf")
                self.open_pdf(config['output_file'])
            else:
                self.show_message("Error generando reporte de inventario")
        except Exception as e:
            self.show_message(f"Error generando inventario: {str(e)}")
            traceback.print_exc()

    def generate_sales_report(self):
        try:
            sales = self.db.get_sales_report()
            if not sales:
                self.show_message("¡No hay ventas registradas!")
                return
            config = {
                'title': 'Reporte de Ventas',
                'subtitle': 'Historial de Transacciones',
                'logo_path': './logo.png' if os.path.exists('./logo.png') else None,
                'output_file': 'sales_report.pdf',
                'introduction': 'Detalle completo de todas las transacciones comerciales realizadas.',
                'author': 'Sistema de Gestión TireStore'
            }
            formatted_sales = [{
                "ID": s[0],
                "Fecha": datetime.strptime(s[1], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M"),
                "Total": f"₡{s[2]:,.2f}",
                "Cliente": s[3] if s[3] else "Consumidor Final",
                "Productos": s[4]
            } for s in sales]
            if generate_professional_report({'sales': formatted_sales}, config):
                self.show_message("Reporte de ventas generado: sales_report.pdf")
                self.open_pdf(config['output_file'])
            else:
                self.show_message("Error generando reporte de ventas")
        except Exception as e:
            self.show_message(f"Error generando ventas: {str(e)}")
            traceback.print_exc()

    def generate_customers_report(self):
        try:
            customers = self.db.get_customers()
            if not customers:
                self.show_message("¡No hay clientes registrados!")
                return
            config = {
                'title': 'Reporte de Clientes',
                'subtitle': 'Base de Datos de Clientes',
                'logo_path': './logo.png' if os.path.exists('./logo.png') else None,
                'output_file': 'customers_report.pdf',
                'introduction': 'Listado completo de clientes registrados en el sistema.',
                'author': 'Sistema de Gestión TireStore'
            }
            formatted_customers = [{
                "ID": c[0],
                "Nombre": c[1],
                "Teléfono": c[2] if c[2] else "N/A",
                "Email": c[3] if c[3] else "N/A",
                "Dirección": c[4] if c[4] else "N/A"
            } for c in customers]
            if generate_professional_report({'customers': formatted_customers}, config):
                self.show_message("Reporte de clientes generado: customers_report.pdf")
                self.open_pdf(config['output_file'])
            else:
                self.show_message("Error generando reporte de clientes")
        except Exception as e:
            self.show_message(f"Error generando clientes: {str(e)}")
            traceback.print_exc()

    def generate_full_report(self):
        # Implementación del reporte completo
        pass

    def open_pdf(self, filename):
        try:
            if platform == 'win':
                os.startfile(filename)
            elif platform == 'linux':
                subprocess.call(('xdg-open', filename))
            elif platform == 'darwin':
                subprocess.call(('open', filename))
        except Exception as e:
            print(f"Error abriendo PDF: {str(e)}")

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'main'

class SettingsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.load_settings()

    def load_settings(self):
        try:
            # Cargar configuraciones guardadas o usar valores predeterminados
            if not hasattr(self.app, 'settings'):
                self.app.settings = {
                    'theme': 'Claro',
                    'language': 'Español'
                }
            
            # Aplicar tema guardado
            if self.ids.theme_spinner:
                self.ids.theme_spinner.text = self.app.settings['theme']
            
            # Aplicar idioma guardado
            if self.ids.language_spinner:
                self.ids.language_spinner.text = self.app.settings['language']

            self.apply_theme(self.app.settings['theme'])
            self.apply_language(self.app.settings['language'])

        except Exception as e:
            self.show_message(f"Error cargando configuración: {str(e)}")

    def save_settings(self):
        try:
            # Guardar configuraciones
            self.app.settings = {
                'theme': self.ids.theme_spinner.text,
                'language': self.ids.language_spinner.text
            }
            
            # Aplicar cambios
            self.apply_theme(self.app.settings['theme'])
            self.apply_language(self.app.settings['language'])
            
            self.show_message("Configuración guardada correctamente")
        except Exception as e:
            self.show_message(f"Error guardando configuración: {str(e)}")

    def apply_theme(self, theme):
        try:
            if theme == 'Oscuro':
                # Colores para tema oscuro
                self.app.theme = {
                    'primary_color': (0.2, 0.6, 0.8, 1),
                    'secondary_color': (0.31, 0.43, 0.48, 1),
                    'accent_color': (0.8, 0.2, 0.2, 1),
                    'text_color': (0.9, 0.9, 0.9, 1),
                    'bg_color': (0.15, 0.15, 0.15, 1),
                    'input_bg': (0.2, 0.2, 0.2, 1)
                }
                Window.clearcolor = (0.1, 0.1, 0.1, 1)
                
                # Actualizar colores de widgets
                for screen in self.manager.screens:
                    if hasattr(screen, 'canvas'):
                        screen.canvas.before.children[1].rgba = (0.15, 0.15, 0.15, 1)
                    
                    # Actualizar colores de labels
                    for widget in screen.walk():
                        if isinstance(widget, Label):
                            widget.color = (0.9, 0.9, 0.9, 1)
                        elif isinstance(widget, TextInput):
                            widget.background_color = (0.2, 0.2, 0.2, 1)
                            widget.foreground_color = (0.9, 0.9, 0.9, 1)
                        elif isinstance(widget, Button) and not isinstance(widget, CustomButton):
                            widget.background_color = (0.3, 0.3, 0.3, 1)
                            widget.color = (0.9, 0.9, 0.9, 1)

            else:  # Tema claro
                self.app.theme = {
                    'primary_color': (0.2, 0.6, 0.8, 1),
                    'secondary_color': (0.31, 0.43, 0.48, 1),
                    'accent_color': (0.8, 0.2, 0.2, 1),
                    'text_color': (0.2, 0.2, 0.2, 1),
                    'bg_color': (0.95, 0.95, 0.95, 1),
                    'input_bg': (1, 1, 1, 1)
                }
                Window.clearcolor = (1, 1, 1, 1)
                
                # Actualizar colores de widgets
                for screen in self.manager.screens:
                    if hasattr(screen, 'canvas'):
                        screen.canvas.before.children[1].rgba = (0.95, 0.95, 0.95, 1)
                    
                    # Actualizar colores de labels
                    for widget in screen.walk():
                        if isinstance(widget, Label):
                            widget.color = (0.2, 0.2, 0.2, 1)
                        elif isinstance(widget, TextInput):
                            widget.background_color = (1, 1, 1, 1)
                            widget.foreground_color = (0.2, 0.2, 0.2, 1)
                        elif isinstance(widget, Button) and not isinstance(widget, CustomButton):
                            widget.background_color = (0.9, 0.9, 0.9, 1)
                            widget.color = (0.2, 0.2, 0.2, 1)

        except Exception as e:
            self.show_message(f"Error aplicando tema: {str(e)}")

    def apply_language(self, language):
        try:
            translations = {
                'Español': {
                    'login': 'Iniciar Sesión',
                    'username': 'Usuario',
                    'password': 'Contraseña',
                    'products': 'Productos',
                    'sales': 'Ventas',
                    'customers': 'Clientes',
                    'reports': 'Reportes',
                    'settings': 'Configuración',
                    'logout': 'Cerrar Sesión',
                    'save': 'Guardar',
                    'back': 'Volver',
                    'add': 'Añadir',
                    'view': 'Ver',
                    'name': 'Nombre',
                    'phone': 'Teléfono',
                    'email': 'Correo',
                    'address': 'Dirección',
                    'product': 'Producto',
                    'brand': 'Marca',
                    'size': 'Tamaño',
                    'type': 'Tipo',
                    'price': 'Precio',
                    'stock': 'Stock',
                    'quantity': 'Cantidad',
                    'customer': 'Cliente',
                    'date': 'Fecha',
                    'total': 'Total',
                    'save_changes': 'Guardar Cambios',
                    'back_to_menu': 'Volver al Menú Principal',
                    'select_product': 'Seleccionar Producto',
                    'select_customer': 'Seleccionar Cliente',
                    'register_sale': 'Registrar Venta',
                    'view_history': 'Ver Historial',
                    'add_customer': 'Añadir Cliente',
                    'view_customers': 'Ver Clientes',
                    'system_settings': 'Configuración del Sistema',
                    'theme': 'Tema',
                    'language': 'Idioma'
                },
                'English': {
                    'login': 'Login',
                    'username': 'Username',
                    'password': 'Password',
                    'products': 'Products',
                    'sales': 'Sales',
                    'customers': 'Customers',
                    'reports': 'Reports',
                    'settings': 'Settings',
                    'logout': 'Logout',
                    'save': 'Save',
                    'back': 'Back',
                    'add': 'Add',
                    'view': 'View',
                    'name': 'Name',
                    'phone': 'Phone',
                    'email': 'Email',
                    'address': 'Address',
                    'product': 'Product',
                    'brand': 'Brand',
                    'size': 'Size',
                    'type': 'Type',
                    'price': 'Price',
                    'stock': 'Stock',
                    'quantity': 'Quantity',
                    'customer': 'Customer',
                    'date': 'Date',
                    'total': 'Total',
                    'save_changes': 'Save Changes',
                    'back_to_menu': 'Back to Main Menu',
                    'select_product': 'Select Product',
                    'select_customer': 'Select Customer',
                    'register_sale': 'Register Sale',
                    'view_history': 'View History',
                    'add_customer': 'Add Customer',
                    'view_customers': 'View Customers',
                    'system_settings': 'System Settings',
                    'theme': 'Theme',
                    'language': 'Language'
                }
            }
            
            self.app.translations = translations[language]
            self.update_ui_texts()
            
        except Exception as e:
            self.show_message(f"Error aplicando idioma: {str(e)}")

    def update_ui_texts(self):
        try:
            for screen in self.manager.screens:
                if isinstance(screen, LoginScreen):
                    screen.ids.username.hint_text = self.app.translations['username']
                    screen.ids.password.hint_text = self.app.translations['password']
                
                elif isinstance(screen, MainScreen):
                    for child in screen.walk():
                        if isinstance(child, Button):
                            if '📦' in child.text:
                                child.text = f"📦 {self.app.translations['products']}"
                            elif '💰' in child.text:
                                child.text = f"💰 {self.app.translations['sales']}"
                            elif '👥' in child.text:
                                child.text = f"👥 {self.app.translations['customers']}"
                            elif '📊' in child.text:
                                child.text = f"📊 {self.app.translations['reports']}"
                            elif '⚙️' in child.text:
                                child.text = f"⚙️ {self.app.translations['settings']}"
                            elif child.text == 'Cerrar Sesión':
                                child.text = self.app.translations['logout']
                
                elif isinstance(screen, ProductScreen):
                    screen.ids.name.hint_text = self.app.translations['name']
                    screen.ids.brand.hint_text = self.app.translations['brand']
                    screen.ids.size.hint_text = self.app.translations['size']
                    screen.ids.type.text = self.app.translations['select_product']
                    screen.ids.price.hint_text = self.app.translations['price']
                    screen.ids.stock.hint_text = self.app.translations['stock']
                
                elif isinstance(screen, SalesScreen):
                    screen.ids.product_spinner.text = self.app.translations['select_product']
                    screen.ids.quantity_input.hint_text = self.app.translations['quantity']
                    screen.ids.customer_spinner.text = self.app.translations['select_customer']
                
                elif isinstance(screen, CustomersScreen):
                    screen.ids.name_input.hint_text = self.app.translations['name']
                    screen.ids.phone_input.hint_text = self.app.translations['phone']
                    screen.ids.email_input.hint_text = self.app.translations['email']
                    screen.ids.address_input.hint_text = self.app.translations['address']

        except Exception as e:
            self.show_message(f"Error actualizando textos: {str(e)}")

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'main'

class TireStoreApp(App):
    def build(self):
        try:
            # El archivo .kv se cargará automáticamente si su nombre coincide
            # con el nombre de la clase (en minúsculas sin 'App')
            # En este caso buscará 'tirestore.kv'
            # Configurar la ventana principal
            Window.clearcolor = (1, 1, 1, 1)  # Fondo blanco
            # Crear el administrador de pantallas
            sm = ScreenManager()
            # Añadir todas las pantallas
            sm.add_widget(LoginScreen(name='login'))
            sm.add_widget(MainScreen(name='main'))
            sm.add_widget(ProductScreen(name='products'))
            sm.add_widget(SalesScreen(name='sales'))
            sm.add_widget(CustomersScreen(name='customers'))
            sm.add_widget(ReportsScreen(name='reports'))
            sm.add_widget(SettingsScreen(name='settings'))
            return sm
        except Exception as e:
            print(f"Error iniciando la aplicación: {str(e)}")
            return Label(text='Error iniciando la aplicación')
if __name__ == '__main__':
    try:
        # Inicializar la base de datos
        db = DatabaseManager()
        # Iniciar la aplicación
        TireStoreApp().run()
    except Exception as e:
        print(f"Error fatal: {str(e)}")
        print(traceback.format_exc())
