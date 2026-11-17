import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import CreditTransaction, UploadedDocument, UserCredit
from .processor import BlackBoxProcessor

TOKEN_COST_PER_UPLOAD = 5


def home(request):
    total_docs = 0
    recent_docs = []
    if request.user.is_authenticated:
        total_docs = UploadedDocument.objects.filter(user=request.user).count()
        recent_docs = UploadedDocument.objects.filter(user=request.user)[:3]

    return render(request, 'main/home.html', {
        'total_docs': total_docs,
        'recent_docs': recent_docs,
        'token_cost': TOKEN_COST_PER_UPLOAD,
    })


@login_required
def profile_view(request):
    credit, _ = UserCredit.objects.get_or_create(user=request.user, defaults={'tokens': 100})
    user_docs = UploadedDocument.objects.filter(user=request.user)
    completed_count = user_docs.filter(status='completed').count()
    pending_count = user_docs.filter(status='pending').count()
    transactions = CreditTransaction.objects.filter(credit=credit)[:5]

    return render(request, 'profile.html', {
        'credit': credit,
        'total_docs': user_docs.count(),
        'completed_count': completed_count,
        'pending_count': pending_count,
        'recent_transactions': transactions,
    })


@login_required
def settings_view(request):
    return render(request, 'settings.html')


@login_required
def documents_view(request):
    credit, _ = UserCredit.objects.get_or_create(user=request.user, defaults={'tokens': 100})

    if request.method == 'POST':
        file = request.FILES.get('document_file')
        if not file:
            messages.error(request, 'Please select a document or image file to upload.')
            return redirect('documents')

        # Check maximum file size (25MB)
        if file.size > 25 * 1024 * 1024:
            messages.error(request, 'The uploaded file exceeds the 25MB maximum limit.')
            return redirect('documents')

        # Check credit balance
        if not credit.can_afford(TOKEN_COST_PER_UPLOAD):
            messages.error(
                request,
                f'Insufficient tokens! You need {TOKEN_COST_PER_UPLOAD} tokens to upload and process a document, '
                f'but your balance is {credit.tokens} tokens. Please recharge your tokens below.'
            )
            return redirect('documents')

        title = request.POST.get('title', '').strip()
        doc_type = request.POST.get('doc_type', 'receipt')
        output_format = request.POST.get('output_format', 'both')
        process_mode = request.POST.get('process_mode', 'immediate')

        # Deduct credit and create document inside transaction logic
        doc = UploadedDocument.objects.create(
            user=request.user,
            title=title,
            doc_type=doc_type,
            output_format=output_format,
            file=file,
            original_filename=file.name,
            file_size=file.size,
            content_type=file.content_type or '',
            tokens_cost=TOKEN_COST_PER_UPLOAD,
            status='pending',
        )

        credit.deduct(
            amount=TOKEN_COST_PER_UPLOAD,
            description=f"Upload & conversion of {doc.original_filename}",
            document=doc,
        )

        # Trigger Black Box processing
        BlackBoxProcessor.process_document(doc, mode=process_mode)

        if process_mode == 'immediate':
            messages.success(
                request,
                f"Successfully uploaded '{doc.display_title}'! The black-box converter generated your formatted JSON and SQL data ({TOKEN_COST_PER_UPLOAD} tokens used)."
            )
        else:
            messages.info(
                request,
                f"Document '{doc.display_title}' uploaded and marked as pending for external conversion system ({TOKEN_COST_PER_UPLOAD} tokens used)."
            )

        return redirect('documents')

    # GET request - list documents with search & filter
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()

    docs = UploadedDocument.objects.filter(user=request.user)

    if query:
        docs = docs.filter(
            Q(title__icontains=query) |
            Q(original_filename__icontains=query) |
            Q(extracted_text__icontains=query)
        )

    if status_filter:
        docs = docs.filter(status=status_filter)

    if type_filter:
        docs = docs.filter(doc_type=type_filter)

    paginator = Paginator(docs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # User statistics
    total_uploads = UploadedDocument.objects.filter(user=request.user).count()
    completed_uploads = UploadedDocument.objects.filter(user=request.user, status='completed').count()
    pending_uploads = UploadedDocument.objects.filter(user=request.user, status='pending').count()
    transactions = CreditTransaction.objects.filter(credit=credit)[:10]

    return render(request, 'main/documents.html', {
        'page_obj': page_obj,
        'credit': credit,
        'token_cost': TOKEN_COST_PER_UPLOAD,
        'total_uploads': total_uploads,
        'completed_uploads': completed_uploads,
        'pending_uploads': pending_uploads,
        'transactions': transactions,
        'search_query': query,
        'status_filter': status_filter,
        'type_filter': type_filter,
    })


@login_required
def document_detail_api(request, doc_id):
    """Return JSON details of a document for modal preview and inspection."""
    doc = get_object_or_404(UploadedDocument, id=doc_id, user=request.user)
    
    return JsonResponse({
        'id': doc.id,
        'title': doc.display_title,
        'original_filename': doc.original_filename,
        'doc_type': doc.doc_type,
        'doc_type_display': doc.get_doc_type_display(),
        'output_format': doc.output_format,
        'file_url': doc.file.url if doc.file else None,
        'file_size': doc.formatted_size,
        'status': doc.status,
        'status_display': doc.get_status_display(),
        'tokens_cost': doc.tokens_cost,
        'extracted_text': doc.extracted_text,
        'json_output': doc.json_output,
        'sql_output': doc.sql_output,
        'error_message': doc.error_message,
        'is_image': doc.is_image,
        'created_at': doc.created_at.strftime('%b %d, %Y %H:%M'),
        'completed_at': doc.completed_at.strftime('%b %d, %Y %H:%M') if doc.completed_at else None,
    })


@login_required
def document_download_file(request, doc_id):
    """Download original document file."""
    doc = get_object_or_404(UploadedDocument, id=doc_id, user=request.user)
    if not doc.file or not doc.file.storage.exists(doc.file.name):
        raise Http404("File does not exist.")
    return FileResponse(doc.file.open('rb'), as_attachment=True, filename=doc.original_filename)


@login_required
def document_download_output(request, doc_id, format_type):
    """Download formatted JSON or SQL output file."""
    doc = get_object_or_404(UploadedDocument, id=doc_id, user=request.user)
    clean_base = (doc.title or doc.original_filename).replace(' ', '_')

    if format_type == 'json':
        data = json.dumps(doc.json_output or {}, indent=2)
        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{clean_base}_output.json"'
        return response
    elif format_type == 'sql':
        data = doc.sql_output or '-- No SQL generated'
        response = HttpResponse(data, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{clean_base}_output.sql"'
        return response
    elif format_type == 'text':
        data = doc.extracted_text or 'No text extracted'
        response = HttpResponse(data, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{clean_base}_raw_text.txt"'
        return response
    else:
        raise Http404("Invalid format requested.")


@login_required
@require_POST
def topup_credits_view(request):
    """Allow user to top up or claim test credits."""
    credit, _ = UserCredit.objects.get_or_create(user=request.user, defaults={'tokens': 100})
    amount = int(request.POST.get('amount', 50))
    if amount <= 0 or amount > 500:
        amount = 50

    credit.topup(amount=amount, description=f"Top-up of +{amount} tokens")
    messages.success(request, f"Successfully added {amount} tokens to your account! New balance: {credit.tokens} tokens.")
    return redirect(request.META.get('HTTP_REFERER') or 'documents')


@login_required
@require_POST
def reprocess_document_view(request, doc_id):
    """Re-run the black box conversion on an uploaded document."""
    doc = get_object_or_404(UploadedDocument, id=doc_id, user=request.user)
    BlackBoxProcessor.process_document(doc, mode='immediate')
    messages.success(request, f"Re-processed '{doc.display_title}' through the black-box converter.")
    return redirect('documents')


@login_required
@require_POST
def delete_document_view(request, doc_id):
    """Delete an uploaded document record and file."""
    doc = get_object_or_404(UploadedDocument, id=doc_id, user=request.user)
    name = doc.display_title
    if doc.file:
        try:
            doc.file.delete(save=False)
        except Exception:
            pass
    doc.delete()
    messages.info(request, f"Document '{name}' deleted.")
    return redirect('documents')


# ==============================================================================
# External System Black-Box API endpoints
# Used by external scripts or microservices that handle OCR/conversion
# ==============================================================================

def api_pending_documents(request):
    """
    Public or worker API endpoint: returns list of documents awaiting black-box processing.
    """
    docs = UploadedDocument.objects.filter(status='pending').order_by('created_at')[:50]
    data = []
    for d in docs:
        data.append({
            'id': d.id,
            'title': d.display_title,
            'doc_type': d.doc_type,
            'original_filename': d.original_filename,
            'file_url': request.build_absolute_uri(d.file.url) if d.file else None,
            'output_format': d.output_format,
            'created_at': d.created_at.isoformat(),
        })
    return JsonResponse({'pending_count': len(data), 'documents': data})


@csrf_exempt
@require_POST
def api_submit_result(request, doc_id):
    """
    External converter worker endpoint: submits converted OCR text, JSON, and SQL.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    extracted_text = payload.get('extracted_text')
    json_output = payload.get('json_output')
    sql_output = payload.get('sql_output')
    status = payload.get('status', 'completed')
    error_message = payload.get('error_message', '')

    success, msg = BlackBoxProcessor.apply_external_result(
        document_id=doc_id,
        extracted_text=extracted_text,
        json_output=json_output,
        sql_output=sql_output,
        status=status,
        error_message=error_message,
    )

    if success:
        return JsonResponse({'success': True, 'message': msg})
    return JsonResponse({'error': msg}, status=404 if 'not found' in msg else 400)
