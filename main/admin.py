from django.contrib import admin
from .models import CreditTransaction, UploadedDocument, UserCredit


@admin.register(UserCredit)
class UserCreditAdmin(admin.ModelAdmin):
    list_display = ('user', 'tokens', 'total_spent', 'updated_at')
    search_fields = ('user__username', 'user__email')


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'original_filename', 'doc_type', 'user', 'status', 'tokens_cost', 'created_at')
    list_filter = ('doc_type', 'status', 'output_format', 'created_at')
    search_fields = ('title', 'original_filename', 'user__username', 'extracted_text')
    readonly_fields = ('file_size', 'content_type', 'created_at', 'completed_at')


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ('credit', 'amount', 'balance_after', 'transaction_type', 'description', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('credit__user__username', 'description')
