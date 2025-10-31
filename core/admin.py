import io
import base64
import socket

import qrcode
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import QuizConfig, Contestant, Question, Choice, QuestionImage, Answer


def get_local_ip_address():
    """
    Get the local IP address of the machine running the server.
    Returns the first non-loopback IPv4 address found.
    """
    try:
        # Method 1: Connect to external address to determine active interface
        # This is the most reliable method - determines which interface would route to internet
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't actually connect, just determines which interface would be used
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and ip != '127.0.0.1':
                return ip
        except (socket.error, OSError):
            pass
        finally:
            s.close()
    except (socket.error, OSError):
        pass
    
    # Method 2: Try to get IP from hostname
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        # Check if it's not loopback
        if local_ip and local_ip != '127.0.0.1':
            return local_ip
    except (socket.error, OSError):
        pass
    
    # Method 3: Check all network interfaces
    try:
        # Get all IP addresses associated with hostname
        addrs = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        for addr in addrs:
            ip = addr[4][0]
            # Skip loopback and link-local addresses
            if ip and ip != '127.0.0.1' and not ip.startswith('169.254'):
                return ip
    except (socket.error, OSError, AttributeError):
        pass
    
    # Fallback to localhost
    return '127.0.0.1'


@admin.register(QuizConfig)
class QuizConfigAdmin(admin.ModelAdmin):
    list_display = ("total_allowed_answers_per_user", "quiz_started_at")


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    list_display = ("nickname", "name", "school_name", "phone_number")
    search_fields = ("nickname", "name", "school_name")


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


class QuestionImageInline(admin.TabularInline):
    model = QuestionImage
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at", "qr_code_link")
    list_filter = ("is_active",)
    inlines = [ChoiceInline, QuestionImageInline]
    readonly_fields = ("created_at", "qr_code_display")

    fieldsets = (
        (None, {"fields": ("title", "body", "is_active", "created_at")}),
        ("QR Code", {"fields": ("qr_code_display",)}),
    )

    def _get_base_url(self, request=None):
        """Get the base URL for QR code generation using local IP address."""
        from django.conf import settings
        
        # First check if explicitly set in settings
        if hasattr(settings, "QR_CODE_BASE_URL"):
            return settings.QR_CODE_BASE_URL
        
        # Get local IP address
        local_ip = get_local_ip_address()
        
        # Get port from request or use default
        port = 8000  # Default Django development port
        scheme = "http"
        
        if request:
            scheme = "https" if request.is_secure() else "http"
            host = request.get_host()
            
            # Extract port from host if present (e.g., "192.168.1.100:8000" or "localhost:8000")
            if ':' in host:
                try:
                    port = int(host.split(':')[1])
                except (ValueError, IndexError):
                    pass
            else:
                # Try to get port from server port in request meta
                server_port = request.META.get('SERVER_PORT')
                if server_port:
                    try:
                        port = int(server_port)
                    except (ValueError, TypeError):
                        pass
        
        return f"{scheme}://{local_ip}:{port}"

    def qr_code_link(self, obj):
        """Display link to view QR code in admin change form."""
        if obj.pk:
            from django.urls import reverse
            change_url = reverse("admin:core_question_change", args=[obj.pk])
            return format_html('<a href="{}#qr_code_display">{}</a>', change_url, "📱 Show QR")
        return "-"
    qr_code_link.short_description = "QR Code"

    def qr_code_display(self, obj):
        """Generate and display QR code as inline image."""
        if not obj.pk:
            return "Save the question first to generate QR code."
        
        # Build the question URL
        from django.urls import reverse
        path = reverse("question_entrypoint", args=[obj.id])
        
        # Get request from admin context if available
        request = getattr(self, "_request", None)
        base_url = self._get_base_url(request)
        full_url = f"{base_url}{path}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(full_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # Return HTML with image and URL
        return format_html(
            '<div id="qr_code_display" style="margin: 20px 0;">'
            '<img src="data:image/png;base64,{}" alt="QR Code" style="max-width: 300px; border: 1px solid #ddd; padding: 10px; background: white;" /><br/>'
            '<p style="margin-top: 10px;"><strong>URL:</strong> <a href="{}" target="_blank">{}</a></p>'
            '<p style="margin-top: 5px; color: #666; font-size: 12px;">Scan this QR code or share the URL above</p>'
            '</div>',
            img_str,
            full_url,
            full_url
        )
    qr_code_display.short_description = "QR Code"

    def changeform_view(self, request, *args, **kwargs):
        """Store request for use in readonly fields."""
        self._request = request
        return super().changeform_view(request, *args, **kwargs)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("contestant", "question", "is_correct", "submitted_at")
    list_filter = ("is_correct", "submitted_at")
    search_fields = ("contestant__nickname", "question__title")
