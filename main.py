import os
import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import get_color_from_hex, platform
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty, StringProperty, BooleanProperty

class SmartLabel(BoxLayout):
    text = StringProperty('')
    bg_color = StringProperty('#ffffff')
    is_header = BooleanProperty(False)
    fixed_width = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(40)
        self.padding = [dp(5), dp(2)]
        
        if self.fixed_width > 0:
            self.size_hint_x = None
            self.width = self.fixed_width
        
        with self.canvas.before:
            Color(*get_color_from_hex(self.bg_color))
            self.rect = Rectangle(size=self.size, pos=self.pos)
            
        self.label = Label(
            text=self.text,
            size_hint_y=None,
            height=self.height,
            halign='left',
            valign='center',
            text_size=(None, None),
            font_size=dp(14) if not self.is_header else dp(16),
            bold=self.is_header,
            color=get_color_from_hex('#333333') if not self.is_header else get_color_from_hex('#ffffff')
        )
        self.add_widget(self.label)
        
        self.bind(size=self._update)
        self.bind(pos=self._update)
        
    def _update(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos
        self.label.text_size = (self.width - dp(10), None)

class MobileAnniversaryTracker(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 1
        self.current_filters = {}
        self.current_year = datetime.now().year
        self.db_path = None

    def build(self):
        Window.clearcolor = get_color_from_hex('#f5f5f5')
        Window.size = (dp(800), dp(1200))
        
        # Инициализация базы данных при запуске
        self.db_path = self.get_db_path()
        self.create_database()
        
        self.layout = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(5))
        
        # Top panel
        top_panel = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        self.date_label = Label(
            text=f"Сегодня: {datetime.now().strftime('%d.%m.%Y')}",
            size_hint_x=0.5,
            color=get_color_from_hex('#333333'),
            font_size=dp(16)
        )
        top_panel.add_widget(self.date_label)
        
        self.search_input = TextInput(
            hint_text='Поиск по названию...',
            size_hint_x=0.5,
            multiline=False,
            foreground_color=get_color_from_hex('#333333'),
            background_color=get_color_from_hex('#ffffff'),
            padding=dp(5),
            font_size=dp(16)
        )
        self.search_input.bind(text=self.on_search_text)
        top_panel.add_widget(self.search_input)
        
        # Filter panel
        filter_panel = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        
        self.year_filter = TextInput(
            hint_text='Год юбилея (напр. 2025)',
            size_hint_x=0.4,
            multiline=False,
            input_filter='int',
            foreground_color=get_color_from_hex('#333333'),
            font_size=dp(16),
            padding=dp(5)
        )
        
        year_filter_btn = Button(
            text='Применить год',
            size_hint_x=0.3,
            background_color=get_color_from_hex('#3498db'),
            color=get_color_from_hex('#ffffff'),
            font_size=dp(14)
        )
        year_filter_btn.bind(on_press=self.apply_year_filter)
        
        self.month_spinner = Spinner(
            text='Все месяцы',
            values=('Все месяцы', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'),
            size_hint_x=0.3,
            font_size=dp(14)
        )
        self.month_spinner.bind(text=self.apply_month_filter)
        
        filter_panel.add_widget(self.year_filter)
        filter_panel.add_widget(year_filter_btn)
        filter_panel.add_widget(self.month_spinner)
        
        reset_btn = Button(
            text='Сброс',
            size_hint_x=0.3,
            background_color=get_color_from_hex('#e74c3c'),
            color=get_color_from_hex('#ffffff'),
            font_size=dp(14)
        )
        reset_btn.bind(on_press=self.reset_filters)
        filter_panel.add_widget(reset_btn)
        
        # Main table
        self.scroll = ScrollView(bar_width=dp(10))
        self.table = GridLayout(
            cols=5,
            size_hint_y=None,
            spacing=dp(1),
            padding=dp(1)
        )
        self.table.bind(minimum_height=self.table.setter('height'))
        self.scroll.add_widget(self.table)
        
        # Pagination
        pagination_panel = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        
        self.page_info = Label(
            text='Страница 1 из 1',
            size_hint_x=0.4,
            color=get_color_from_hex('#333333'),
            font_size=dp(14)
        )
        
        prev_btn = Button(
            text='< Назад',
            size_hint_x=0.3,
            background_color=get_color_from_hex('#7f8c8d'),
            color=get_color_from_hex('#ffffff'),
            font_size=dp(14)
        )
        prev_btn.bind(on_press=self.prev_page)
        
        next_btn = Button(
            text='Вперед >',
            size_hint_x=0.3,
            background_color=get_color_from_hex('#7f8c8d'),
            color=get_color_from_hex('#ffffff'),
            font_size=dp(14)
        )
        next_btn.bind(on_press=self.next_page)
        
        pagination_panel.add_widget(prev_btn)
        pagination_panel.add_widget(self.page_info)
        pagination_panel.add_widget(next_btn)
        
        self.layout.add_widget(top_panel)
        self.layout.add_widget(filter_panel)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(pagination_panel)
        
        self.load_data()
        
        return self.layout
    
    def get_db_path(self):
        """Получает правильный путь к базе данных в зависимости от платформы"""
        if platform == 'android':
            try:
                from android.storage import app_storage_path
                db_dir = app_storage_path()
                if not os.path.exists(db_dir):
                    os.makedirs(db_dir)
                return os.path.join(db_dir, 'companies.db')
            except Exception:
                # Если что-то пошло не так, используем стандартный путь
                return 'companies.db'
        else:
            return 'companies.db'
    
    def create_database(self):
        """Создает базу данных, если она не существует"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем, существует ли таблица
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
            if not cursor.fetchone():
                cursor.execute('''CREATE TABLE companies (
                                    id INTEGER PRIMARY KEY,
                                    name TEXT UNIQUE,
                                    website TEXT,
                                    anniversary_date TEXT,
                                    jubilee TEXT,
                                    industry TEXT,
                                    calls TEXT,
                                    notes TEXT)''')
                conn.commit()
                
                # Добавляем тестовые данные, если нужно
                # cursor.execute("INSERT INTO companies (name, anniversary_date) VALUES (?, ?)", 
                #               ("Пример компании", "01.01.2000"))
                # conn.commit()
                
        except sqlite3.Error as e:
            self.show_error(f"Ошибка при создании базы данных: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def load_data(self, page=1):
        """Загружает данные из базы данных с учетом фильтров и пагинации"""
        conn = None
        try:
            self.table.clear_widgets()
            self.current_page = page
            
            # Заголовки таблицы
            headers = ["№", "Компания", "Отрасль", "Дата", "Юбилей"]
            for h in headers:
                self.table.add_widget(SmartLabel(
                    text=h,
                    bg_color='#3498db',
                    is_header=True,
                    fixed_width=dp(40) if h == "№" else 0
                ))
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            conditions = ["anniversary_date != '0' AND anniversary_date != ''"]
            params = []
            
            # Фильтр по году
            if 'year' in self.current_filters and self.current_filters['year'].isdigit():
                year = int(self.current_filters['year'])
                conditions.append("""
                    (? - CAST(SUBSTR(anniversary_date, 7, 4) AS INTEGER)) % 5 = 0
                """)
                params.append(year)
            
            # Фильтр по месяцу
            elif 'month' in self.current_filters and self.current_filters['month'] > 0:
                month = self.current_filters['month']
                conditions.append("SUBSTR(anniversary_date, 4, 2) = ?")
                params.append(f"{month:02d}")
                
                conditions.append("""
                    (? - CAST(SUBSTR(anniversary_date, 7, 4) AS INTEGER)) % 5 = 0
                """)
                params.append(self.current_year)
            
            # Поиск
            if 'search' in self.current_filters:
                conditions.append("(name LIKE ? OR industry LIKE ?)")
                params.extend([f'%{self.current_filters["search"]}%', f'%{self.current_filters["search"]}%'])
            
            # Формируем запрос
            query = f"""
                SELECT rowid, name, industry, anniversary_date, jubilee 
                FROM companies
                WHERE {' AND '.join(conditions)}
                ORDER BY name
                LIMIT ? OFFSET ?
            """
            
            # Добавляем параметры пагинации
            pagination_params = [self.page_size, (page - 1) * self.page_size]
            full_params = params + pagination_params
            
            cursor.execute(query, full_params)
            rows = cursor.fetchall()
            
            # Заполняем таблицу данными
            for i, row in enumerate(rows, 1):
                global_index = (page - 1) * self.page_size + i
                bg_color = '#f8f9fa' if global_index % 2 == 0 else '#ffffff'
                
                self.table.add_widget(SmartLabel(
                    text=str(global_index),
                    bg_color=bg_color,
                    fixed_width=dp(40)
                ))
                
                for col, item in enumerate(row[1:]):
                    self.table.add_widget(SmartLabel(
                        text=str(item) if item else "-",
                        bg_color=bg_color,
                        fixed_width=0
                    ))
            
            # Обновляем информацию о страницах
            count_query = f"SELECT COUNT(*) FROM companies WHERE {' AND '.join(conditions)}"
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]
            self.total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
            self.page_info.text = f"Страница {self.current_page} из {self.total_pages}"
        
        except sqlite3.Error as e:
            self.show_error(f"Ошибка базы данных: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def apply_year_filter(self, instance):
        """Применяет фильтр по году"""
        year = self.year_filter.text.strip()
        if year and year.isdigit() and len(year) == 4:
            self.current_filters = {'year': year}
            self.month_spinner.text = 'Все месяцы'
        else:
            self.current_filters.pop('year', None)
        self.current_page = 1
        self.load_data()
    
    def apply_month_filter(self, instance, value):
        """Применяет фильтр по месяцу"""
        if value == 'Все месяцы':
            self.current_filters.pop('month', None)
        else:
            months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                     'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
            self.current_filters = {'month': months.index(value) + 1}
            self.year_filter.text = ""
        self.current_page = 1
        self.load_data()
    
    def on_search_text(self, instance, value):
        """Обрабатывает поисковый запрос"""
        value = value.strip().lower()
        if len(value) >= 2:
            self.current_filters['search'] = value
        elif 'search' in self.current_filters:
            del self.current_filters['search']
        self.current_page = 1
        self.load_data()
    
    def reset_filters(self, instance):
        """Сбрасывает все фильтры"""
        self.current_filters = {}
        self.year_filter.text = ""
        self.month_spinner.text = 'Все месяцы'
        self.search_input.text = ""
        self.current_page = 1
        self.load_data()
    
    def prev_page(self, instance):
        """Переход на предыдущую страницу"""
        if self.current_page > 1:
            self.load_data(self.current_page - 1)
    
    def next_page(self, instance):
        """Переход на следующую страницу"""
        if self.current_page < self.total_pages:
            self.load_data(self.current_page + 1)
    
    def show_error(self, message):
        """Показывает всплывающее окно с ошибкой"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(
            text=message,
            font_size=dp(16),
            color=get_color_from_hex('#333333')
        ))
        
        btn = Button(
            text='OK',
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#3498db'),
            color=get_color_from_hex('#ffffff')
        )
        
        popup = Popup(
            title='Ошибка',
            title_size=dp(18),
            content=content,
            size_hint=(0.8, 0.4),
            background_color=get_color_from_hex('#f5f5f5')[:3]
        )
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

if __name__ == '__main__':
    MobileAnniversaryTracker().run()