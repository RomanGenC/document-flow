import os
import re
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import Dict, Any, List

import docx
import pdfkit
import pythoncom
import win32com.client
from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from convertors.base_converter import DocumentConverter


class HtmlToPdfConverter(DocumentConverter):
    """Конвертер HTML-контента в PDF-документы с использованием wkhtmltopdf"""

    DEFAULT_PAGE_SIZE = 'A4'
    DEFAULT_MARGIN = '40px'
    DEFAULT_CSS = {
        'body': {'padding': '0', 'font-family': 'Arial, sans-serif'},
        '@page': {'margin': DEFAULT_MARGIN}
    }

    def __init__(self):
        super().__init__()
        self.path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        self.config = pdfkit.configuration(wkhtmltopdf=self.path_to_wkhtmltopdf)

    def get_conversion_options(self) -> Dict[str, Any]:
        """Возвращает параметры конвертации"""
        return {
            'no-images': False,
            'enable-local-file-access': True,
            'quiet': None,
            'page-size': self.DEFAULT_PAGE_SIZE,
            'print-media-type': True,
            'encoding': 'UTF-8'
        }

    def _generate_css(self) -> str:
        """Генерирует CSS стили из DEFAULT_CSS"""
        css_lines = []
        for selector, properties in self.DEFAULT_CSS.items():
            props = '; '.join(f'{k}: {v}' for k, v in properties.items())
            css_lines.append(f'{selector} {{ {props} }}')
        return '\n'.join(css_lines)

    def _prepare_html_content(self, html_content: str) -> str:
        """Добавляет необходимые стили и мета-теги в HTML"""
        return f'<head><meta charset="UTF-8"></head>' + re.sub(
            r'<style>',
            f'<style>{self._generate_css()}',
            html_content,
        )

    def convert(self, file_name: str, request) -> SimpleUploadedFile:
        """
        Конвертирует HTML-контент в PDF-документ

        Args:
            file_name: Базовое имя для выходного файла
            request: Объект запроса с параметрами

        Returns:
            SimpleUploadedFile: Результирующий PDF-документ

        Raises:
            ValueError: При отсутствии обязательных данных
            RuntimeError: При ошибках конвертации
        """
        html_content = request.POST.get('file_content')
        if not html_content:
            raise ValueError('Отсутствует HTML-контент для конвертации')

        try:
            processed_html = self._prepare_html_content(html_content)
            pdf_bytes = pdfkit.from_string(
                input=processed_html,
                output_path=False,
                options=self.get_conversion_options(),
            )
            return self._create_pdf_file(file_name, pdf_bytes)
        except Exception as e:
            raise e

    @staticmethod
    def _create_pdf_file(file_name: str, content: bytes) -> SimpleUploadedFile:
        """Создает объект SimpleUploadedFile для PDF"""
        file_name = f"{file_name.rsplit('.', 1)[0]}.pdf"
        return SimpleUploadedFile(
            name=file_name,
            content=content,
            content_type='application/pdf'
        )


class ImageToPdfConverter(DocumentConverter):
    """Конвертер изображений в PDF документы с поддержкой многопоточности"""

    SUPPORTED_FORMATS = {'image/jpeg', 'image/png', 'image/bmp', 'image/gif'}
    DEFAULT_QUALITY = 90
    PDF_RESOLUTION = 300  # DPI

    def __init__(self):
        super().__init__()
        self._image_objects = []

    def convert(self, file_name: str, request) -> SimpleUploadedFile:
        """
        Конвертирует одно или несколько изображений в PDF

        Args:
            file_name: Базовое имя для выходного файла
            request: Объект запроса с файлами изображений

        Returns:
            SimpleUploadedFile: Результирующий PDF документ

        Raises:
            ValueError: При отсутствии изображений или ошибках валидации
            RuntimeError: При ошибках обработки изображений
        """
        try:
            self._validate_request(request)
            images = self._load_images(request)
            return self._create_pdf(file_name, images)
        except Exception as e:
            raise e

    def _validate_request(self, request) -> None:
        """Проверяет корректность входящего запроса"""
        if not request.FILES.getlist('file_content[]'):
            raise ValueError('Отсутствуют файлы изображений')

        if len(request.FILES.getlist('file_content[]')) == 0:
            raise ValueError('Не загружено ни одного изображения')

    def _load_images(self, request) -> List[Image.Image]:
        """Загружает и валидирует изображения"""
        images = []
        for img_file in request.FILES.getlist('file_content[]'):
            self._validate_image_format(img_file)
            try:
                img = Image.open(img_file)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                images.append(img)
            except IOError as e:
                raise ValueError(f'Невозможно открыть изображение {img_file.name}') from e

        return images

    def _validate_image_format(self, image_file) -> None:
        """Проверяет MIME-тип изображения"""
        content_type = image_file.content_type
        if content_type not in self.SUPPORTED_FORMATS:
            raise ValueError(f'Неподдерживаемый формат изображения: {content_type}')

    def _create_pdf(self, original_name: str, images: List[Image.Image]) -> SimpleUploadedFile:
        """Создает PDF файл из списка изображений"""
        if not images:
            raise ValueError('Нет изображений для конвертации')

        main_image, *other_images = images
        pdf_buffer = BytesIO()

        try:
            main_image.save(
                pdf_buffer,
                format='PDF',
                save_all=True,
                append_images=other_images,
                quality=self.DEFAULT_QUALITY,
                dpi=(self.PDF_RESOLUTION, self.PDF_RESOLUTION)
            )
        except Exception as e:
            raise RuntimeError('Ошибка генерации PDF') from e

        return self._prepare_output_file(original_name, pdf_buffer)

    def _prepare_output_file(self, base_name: str, buffer: BytesIO) -> SimpleUploadedFile:
        """Создает объект SimpleUploadedFile"""
        buffer.seek(0)
        filename = f'{self._sanitize_name(base_name)}.pdf'
        return SimpleUploadedFile(
            name=filename,
            content=buffer.read(),
            content_type='application/pdf'
        )

    def _sanitize_name(self, name: str) -> str:
        """Очищает имя файла от недопустимых символов"""
        return name.split('.')[0].strip().replace(' ', '_')


class WordToPdfConverter(DocumentConverter):
    """"""

    def __init__(self):
        super().__init__()
        self.use_v2_generation = False

    def convert_word_to_pdf(self, file_name, request):
        """"""
        word_to_pdf_dir = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')
        if not os.path.exists(word_to_pdf_dir):
            os.makedirs(word_to_pdf_dir)

        word_file_path = os.path.join(word_to_pdf_dir, file_name + '.docx')

        with open(word_file_path, 'wb') as temp_file:
            temp_file.write(request.FILES.get('file_content').read())

        doc = docx.Document(word_file_path)
        html_content = "<html><body>"
        for para in doc.paragraphs:
            html_content += f"<p>{para.text}</p>"

        html_content += "</body></html>"
        options = {
            'no-images': False,
            'enable-local-file-access': True,
            'quiet': '',
            'page-size': 'A4',
            'print-media-type': True
        }
        styles = 'body { padding: 0; font-family: Arial, sans-serif; } @page { margin: 40px; }'
        html_with_styles = f'<head><meta charset="UTF-8"></head>' + re.sub(r'<style>', f'<style>{styles}', html_content)

        return SimpleUploadedFile(
            f'{file_name}.pdf',
            pdfkit.from_string(html_with_styles, False, options=options),
            content_type='application/pdf'
        )

    def convert_word_to_pdf_v2(self, file_name, request):
        """"""
        # pythoncom.CoInitialize()
        # word_to_pdf_dir = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')
        # os.makedirs(word_to_pdf_dir, exist_ok=True)
        # pdf_title = file_name.split('.')[0]
        # word_file_path = os.path.join(word_to_pdf_dir, pdf_title + '.docx')
        # print(word_file_path)
        # with open(word_file_path, 'wb') as temp_file:
        #     temp_file.write(file_content.read())
        # print(file_name)
        # try:
        #     word = win32com.client.Dispatch('Word.Application')
        #     doc = word.Documents.Open(word_file_path)
        #     doc.SaveAs(os.path.join(word_to_pdf_dir, pdf_title + '.pdf'), FileFormat=17)  # 17 - это формат PDF
        pythoncom.CoInitialize()

        word_to_pdf_dir = os.path.join(settings.MEDIA_ROOT, 'word_to_pdf')
        os.makedirs(word_to_pdf_dir, exist_ok=True)
        pdf_path = os.path.join(word_to_pdf_dir, f"{file_name}.pdf")

        # Создаем временный файл (он удалится после закрытия)
        with NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            temp_file.write(request.FILES.get('file_content').read())  # Записываем файл
            temp_file_path = temp_file.name  # Получаем путь к файлу

        try:
            word = win32com.client.Dispatch('Word.Application')
            word.Visible = True  # Делаем окно Word видимым для отладки

            print(f"Trying to open: {temp_file_path}")
            assert os.path.exists(temp_file_path), f"Файл {temp_file_path} не существует!"

            doc = word.Documents.Open(temp_file_path)
            doc.SaveAs(pdf_path, FileFormat=17)  # 17 - PDF

            doc.Close()
            word.Quit()
            with open(os.path.join(word_to_pdf_dir, file_name + '.pdf'), 'rb') as temp_file:
                return SimpleUploadedFile(
                    f'{file_name}.pdf',
                    temp_file.read(),
                    content_type='application/pdf'
                )
        finally:
            pythoncom.CoUninitialize()

    def convert(self, file_name, request):
        if self.use_v2_generation:
            return self.convert_word_to_pdf_v2(file_name, request)

        return self.convert_word_to_pdf(file_name, request)


class ImageToGrayscaleConverter(DocumentConverter):
    """Конвертер изображений в черно-белый формат с возможностью сохранения в PDF"""

    JPEG_QUALITY = 95
    PDF_RESOLUTION = 300  # DPI
    DEFAULT_IMAGE_FORMAT = 'JPEG'

    def __init__(self):
        super().__init__()
        self._supported_formats = {'image/jpeg', 'image/png', 'image/bmp'}

    def convert(self, file_name: str, request) -> SimpleUploadedFile:
        """
        Конвертирует загруженное изображение в черно-белый формат
        с возможностью сохранения в PDF

        Args:
            file_name: Исходное имя файла
            request: Объект запроса Django

        Returns:
            SimpleUploadedFile: Конвертированный файл
        """
        self._validate_request(request)

        image_file = request.FILES['file_content']
        image = self._process_image(image_file)
        output_buffer = BytesIO()

        if self._should_convert_to_pdf(request):
            self._save_as_pdf(image, output_buffer)
            content_type = 'application/pdf'
            file_extension = 'pdf'
        else:
            self._save_as_image(image, output_buffer)
            content_type = f'image/{self.DEFAULT_IMAGE_FORMAT.lower()}'
            file_extension = 'jpg'

        return self._create_uploaded_file(
            file_name,
            output_buffer,
            file_extension,
            content_type
        )

    def _validate_request(self, request) -> None:
        """Проверяет корректность запроса"""
        if 'file_content' not in request.FILES:
            raise ValueError("Отсутствует файл изображения")

        content_type = request.FILES['file_content'].content_type
        if content_type not in self._supported_formats:
            raise ValueError(f'Неподдерживаемый формат файла: {content_type}')

    @staticmethod
    def _process_image(image_file) -> Image.Image:
        """Обрабатывает и конвертирует изображение"""
        try:
            return Image.open(image_file).convert('L')
        except IOError as e:
            raise ValueError('Невозможно открыть изображение') from e

    @staticmethod
    def _should_convert_to_pdf(request) -> bool:
        """Определяет необходимость конвертации в PDF"""
        return request.POST.get('convert_to_pdf') == 'on'

    def _save_as_image(self, image: Image.Image, buffer: BytesIO) -> None:
        """Сохраняет изображение в формате JPEG"""
        image.save(
            buffer,
            format=self.DEFAULT_IMAGE_FORMAT,
            quality=self.JPEG_QUALITY,
        )

    def _save_as_pdf(self, image: Image.Image, buffer: BytesIO) -> None:
        """Сохраняет изображение в формате PDF"""
        try:
            image.save(
                buffer,
                format='PDF',
                resolution=self.PDF_RESOLUTION,
                save_all=True,
            )
        except ValueError as e:
            raise RuntimeError('Ошибка генерации PDF') from e

    @staticmethod
    def _create_uploaded_file(
        file_name: str,
        buffer: BytesIO,
        extension: str,
        content_type: str,
    ) -> SimpleUploadedFile:
        """Создает объект SimpleUploadedFile"""
        buffer.seek(0)
        filename = f'{file_name.rsplit('.', 1)[0]}.{extension}'
        return SimpleUploadedFile(
            name=filename,
            content=buffer.read(),
            content_type=content_type,
        )


class PngToJpgConverter(DocumentConverter):
    """Конвертер PNG изображений в JPEG формат с поддержкой прозрачности и валидацией"""

    SUPPORTED_MIME_TYPES = {'image/png', 'image/x-png'}
    DEFAULT_QUALITY = 95
    OUTPUT_FORMAT = 'JPEG'
    RGB_MODE = 'RGB'
    BACKGROUND_COLOR = (255, 255, 255)

    def __init__(self):
        super().__init__()

    def convert(self, file_name: str, request) -> SimpleUploadedFile:
        """
        Конвертирует PNG изображение в JPEG формат с обработкой прозрачности

        Args:
            file_name: Исходное имя файла
            request: Объект запроса Django

        Returns:
            SimpleUploadedFile: Конвертированное изображение в формате JPEG

        Raises:
            ValueError: При ошибках валидации
            RuntimeError: При ошибках конвертации
        """
        self._validate_request(request)
        image_file = request.FILES['file_content']

        try:
            with Image.open(image_file) as img:
                return self._process_image(img, file_name)
        except IOError as e:
            raise RuntimeError('Невозможно обработать изображение') from e

    def _validate_request(self, request) -> None:
        """Проверяет корректность входящего запроса"""
        if 'file_content' not in request.FILES:
            raise ValueError('Отсутствует файл изображения')

        self._validate_mime_type(request.FILES['file_content'])

    def _validate_mime_type(self, file) -> None:
        """Проверяет MIME-тип загружаемого файла"""
        content_type = file.content_type
        if content_type not in self.SUPPORTED_MIME_TYPES:
            raise ValueError(f'Неподдерживаемый формат файла: {content_type}. Ожидается PNG.')

    def _process_image(self, image: Image.Image, base_name: str) -> SimpleUploadedFile:
        """Обрабатывает и конвертирует изображение с учетом прозрачности"""
        buffer = BytesIO()
        try:
            converted_image = self._handle_transparency(image)
            converted_image.save(
                buffer,
                format=self.OUTPUT_FORMAT,
                quality=self.DEFAULT_QUALITY,
                optimize=True,
                subsampling=0,
            )
            buffer.seek(0)

            return self._create_output_file(base_name, buffer)
        except Exception as e:
            raise RuntimeError('Ошибка конвертации в JPEG') from e
        finally:
            buffer.close()

    def _handle_transparency(self, image: Image.Image) -> Image.Image:
        """Добавляет белый фон для изображений с прозрачностью"""
        if image.mode in ('RGBA', 'LA'):
            background = Image.new(self.RGB_MODE, image.size, self.BACKGROUND_COLOR)
            background.paste(image, mask=image.split()[-1])
            return background

        return image.convert(self.RGB_MODE)

    def _create_output_file(self, base_name: str, buffer: BytesIO) -> SimpleUploadedFile:
        """Создает объект SimpleUploadedFile"""
        clean_name = self._sanitize_filename(base_name)
        return SimpleUploadedFile(
            name=f'{clean_name}.jpg',
            content=buffer.read(),
            content_type=f'image/{self.OUTPUT_FORMAT.lower()}'
        )

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Очищает и форматирует имя файла"""
        name = filename.rsplit('.', 1)[0]
        return name.strip().replace(' ', '_')


class BmpToJpgConverter(DocumentConverter):
    """Конвертер BMP изображений в JPEG формат с валидацией и обработкой ошибок"""

    SUPPORTED_MIME_TYPES = {'image/bmp', 'image/x-ms-bmp'}
    DEFAULT_QUALITY = 95
    OUTPUT_FORMAT = 'JPEG'
    RGB_MODE = 'RGB'

    def __init__(self):
        super().__init__()

    def convert(self, file_name: str, request) -> SimpleUploadedFile:
        """
        Конвертирует BMP изображение в JPEG формат

        Args:
            file_name: Исходное имя файла
            request: Объект запроса Django

        Returns:
            SimpleUploadedFile: Конвертированное изображение в формате JPEG

        Raises:
            ValueError: При ошибках валидации
            RuntimeError: При ошибках конвертации
        """
        self._validate_request(request)
        image_file = request.FILES['file_content']

        try:
            with Image.open(image_file) as img:
                return self._process_image(img, file_name)
        except IOError as e:
            raise RuntimeError('Невозможно обработать изображение') from e

    def _validate_request(self, request) -> None:
        """Проверяет корректность входящего запроса"""
        if 'file_content' not in request.FILES:
            raise ValueError('Отсутствует файл изображения')

        self._validate_mime_type(request.FILES['file_content'])

    def _validate_mime_type(self, file) -> None:
        """Проверяет MIME-тип загружаемого файла"""
        content_type = file.content_type
        if content_type not in self.SUPPORTED_MIME_TYPES:
            raise ValueError(f"Неподдерживаемый формат файла: {content_type}. Ожидается BMP.")

    def _process_image(self, image: Image.Image, base_name: str) -> SimpleUploadedFile:
        """Обрабатывает и конвертирует изображение"""
        buffer = BytesIO()
        try:
            converted_image = image.convert(self.RGB_MODE)
            converted_image.save(
                buffer,
                format=self.OUTPUT_FORMAT,
                quality=self.DEFAULT_QUALITY,
                optimize=True
            )
            buffer.seek(0)

            return self._create_output_file(base_name, buffer)
        except Exception as e:
            raise RuntimeError('Ошибка конвертации в JPEG') from e
        finally:
            buffer.close()

    def _create_output_file(self, base_name: str, buffer: BytesIO) -> SimpleUploadedFile:
        """Создает объект SimpleUploadedFile"""
        clean_name = self._sanitize_filename(base_name)
        return SimpleUploadedFile(
            name=f'{clean_name}.jpg',
            content=buffer.read(),
            content_type=f'image/{self.OUTPUT_FORMAT.lower()}'
        )

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Очищает и форматирует имя файла"""
        name = filename.rsplit('.', 1)[0]
        return name.strip().replace(' ', '_')


class ImageToDistortConverter(DocumentConverter):
    """"""

    def __init__(self):
        super().__init__()

    def convert(self, file_name, request):
        image = request.FILES.get('file_content')
        print(image, request.FILES)
        uploaded_file = request.FILES.get('file_content')
        file_bytes = uploaded_file.read()

        # Используем Wand для работы с изображением
        # with WandImage(blob=file_bytes) as img:
        #     # При необходимости переводим в оттенки серого
        #     img.type = 'grayscale'
        #
        #     # Подготавливаем аргументы для перспективного искажения
        #     distort_args = [
        #         0, 0, 20, 10,  # Верхний левый: из (0, 0) в (20, 10)
        #         img.width, 0, img.width - 20, 15,  # Верхний правый
        #         img.width, img.height, img.width - 15, img.height - 20,  # Нижний правый
        #         0, img.height, 10, img.height - 10  # Нижний левый
        #     ]
        #
        #     # Применяем перспективное искажение
        #     img.distort('perspective', distort_args, bestfit=False)
        #
        #     # Получаем PDF в виде blob'а
        #     pdf_blob = img.make_blob(format='pdf')

        # image = Image.open(image).convert('L')
        #
        # strength = 5
        # radius = 200
        # width, height = image.size
        # cx, cy = width / 2, height / 2
        # new_img = Image.new("RGB", (width, height))
        #
        # for x in range(width):
        #     for y in range(height):
        #         dx = x - cx
        #         dy = y - cy
        #         distance = math.sqrt(dx ** 2 + dy ** 2)
        #         if distance < radius:
        #             # Вычисляем угол с учетом эффекта закручивания
        #             angle = math.atan2(dy, dx) + strength * (radius - distance) / radius
        #             new_x = int(cx + distance * math.cos(angle))
        #             new_y = int(cy + distance * math.sin(angle))
        #             if 0 <= new_x < width and 0 <= new_y < height:
        #                 new_img.putpixel((x, y), image.getpixel((new_x, new_y)))
        #         else:
        #             new_img.putpixel((x, y), image.getpixel((x, y)))
        #
        # pdf_buffer = BytesIO()
        # image.save(pdf_buffer, format="PDF", save_all=True)
        # pdf_file = pdf_buffer.getvalue()
        return SimpleUploadedFile(
            file_name,
            'pdf_blob',
            content_type='application/pdf',
        )

