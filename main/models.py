import os
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserCredit(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='credit'
    )
    tokens = models.PositiveIntegerField(default=100)
    total_spent = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_afford(self, amount):
        return self.tokens >= amount

    def deduct(self, amount, description='', document=None):
        if not self.can_afford(amount):
            raise ValueError(f"Insufficient tokens. Required: {amount}, Available: {self.tokens}")
        self.tokens -= amount
        self.total_spent += amount
        self.save(update_fields=['tokens', 'total_spent', 'updated_at'])
        return CreditTransaction.objects.create(
            credit=self,
            amount=-amount,
            balance_after=self.tokens,
            transaction_type='upload',
            description=description or 'Document upload and conversion',
            document=document,
        )

    def topup(self, amount, description='Credit top-up'):
        self.tokens += amount
        self.save(update_fields=['tokens', 'updated_at'])
        return CreditTransaction.objects.create(
            credit=self,
            amount=amount,
            balance_after=self.tokens,
            transaction_type='topup',
            description=description,
        )

    def __str__(self):
        return f"{self.user.username} ({self.tokens} tokens)"


class UploadedDocument(models.Model):
    DOC_TYPES = [
        ('receipt', 'Receipt'),
        ('invoice', 'Invoice'),
        ('record', 'Official Record'),
        ('document', 'General Document'),
        ('image', 'Scanned Image / Photo'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending External System'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    OUTPUT_FORMAT_CHOICES = [
        ('both', 'Both (JSON & SQL)'),
        ('json', 'JSON Only'),
        ('sql', 'SQL Only'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_documents'
    )
    title = models.CharField(max_length=255, blank=True)
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES, default='receipt')
    output_format = models.CharField(max_length=20, choices=OUTPUT_FORMAT_CHOICES, default='both')
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)  # bytes
    content_type = models.CharField(max_length=100, blank=True)

    tokens_cost = models.PositiveIntegerField(default=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')

    extracted_text = models.TextField(blank=True, help_text="Raw OCR or extracted text")
    json_output = models.JSONField(blank=True, null=True, help_text="Structured JSON parsed data")
    sql_output = models.TextField(blank=True, help_text="Generated SQL queries/schema")
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.original_filename

    @property
    def display_title(self):
        return self.title if self.title else self.original_filename

    @property
    def formatted_size(self):
        size = float(self.file_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}" if unit != 'B' else f"{int(size)} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def file_extension(self):
        name = self.original_filename or (self.file.name if self.file else '')
        _, ext = os.path.splitext(name)
        return ext.lower().replace('.', '')

    @property
    def is_image(self):
        return self.file_extension in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp']


class CreditTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('upload', 'Document Upload / Extraction'),
        ('topup', 'Credit Recharge'),
        ('refund', 'Token Refund'),
    ]

    credit = models.ForeignKey(
        UserCredit,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.IntegerField()  # Negative for deduction, positive for topup
    balance_after = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='upload')
    description = models.CharField(max_length=255)
    document = models.ForeignKey(
        UploadedDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.credit.user.username} - {self.amount:+d} ({self.created_at:%Y-%m-%d %H:%M})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_credit(sender, instance, created, **kwargs):
    if created:
        UserCredit.objects.get_or_create(user=instance, defaults={'tokens': 100})
