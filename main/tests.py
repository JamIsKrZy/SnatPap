import json
from io import BytesIO
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import CreditTransaction, UploadedDocument, UserCredit
from .processor import BlackBoxProcessor

User = get_user_model()


class HomePageTests(TestCase):
    def test_home_page_is_available(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Home page')

    def test_authenticated_home_page_shows_profile_dropdown(self):
        user = User.objects.create_user(username='alice', password='pass123')
        self.client.force_login(user)

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View profile')
        self.assertContains(response, 'Settings')
        self.assertContains(response, 'Log out')
        self.assertContains(response, 'Documents')

    def test_profile_and_settings_pages_are_available(self):
        user = User.objects.create_user(username='alice', password='pass123')
        self.client.force_login(user)

        profile_response = self.client.get('/profile/')
        settings_response = self.client.get('/settings/')

        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, 'Profile')
        self.assertEqual(settings_response.status_code, 200)
        self.assertContains(settings_response, 'Settings')


class UserCreditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password123')

    def test_user_credit_is_auto_created(self):
        credit = UserCredit.objects.get(user=self.user)
        self.assertEqual(credit.tokens, 100)

    def test_credit_deduction_and_transaction(self):
        credit = UserCredit.objects.get(user=self.user)
        tx = credit.deduct(amount=10, description="Test deduction")
        self.assertEqual(credit.tokens, 90)
        self.assertEqual(credit.total_spent, 10)
        self.assertEqual(tx.amount, -10)
        self.assertEqual(tx.balance_after, 90)

    def test_insufficient_credit_raises_error(self):
        credit = UserCredit.objects.get(user=self.user)
        credit.tokens = 2
        credit.save()
        self.assertFalse(credit.can_afford(5))
        with self.assertRaises(ValueError):
            credit.deduct(amount=5, description="Should fail")

    def test_credit_topup(self):
        credit = UserCredit.objects.get(user=self.user)
        credit.topup(amount=50, description="Test recharge")
        self.assertEqual(credit.tokens, 150)


class DocumentHubTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='docuser', password='password123')
        self.client.force_login(self.user)

    def test_document_hub_requires_login(self):
        self.client.logout()
        response = self.client.get('/documents/')
        self.assertEqual(response.status_code, 302)

    def test_document_hub_view_renders(self):
        response = self.client.get('/documents/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Document Ingestion')
        self.assertContains(response, '100')  # Available tokens

    def test_successful_document_upload_and_blackbox_conversion(self):
        sample_file = SimpleUploadedFile(
            "receipt_test.txt",
            b"Items: Groceries 45.00, Milk 3.50. Total: 48.50",
            content_type="text/plain"
        )
        response = self.client.post('/documents/', {
            'document_file': sample_file,
            'title': 'Test Grocery Receipt',
            'doc_type': 'receipt',
            'output_format': 'both',
            'process_mode': 'immediate',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        # Verify document created
        doc = UploadedDocument.objects.get(title='Test Grocery Receipt')
        self.assertEqual(doc.status, 'completed')
        self.assertIsNotNone(doc.json_output)
        self.assertIn("receipt_items", doc.sql_output)
        # Verify 5 tokens deducted
        credit = UserCredit.objects.get(user=self.user)
        self.assertEqual(credit.tokens, 95)

    def test_upload_blocked_when_insufficient_tokens(self):
        credit = UserCredit.objects.get(user=self.user)
        credit.tokens = 2
        credit.save()

        sample_file = SimpleUploadedFile("doc.txt", b"Test", content_type="text/plain")
        response = self.client.post('/documents/', {
            'document_file': sample_file,
            'title': 'Should Fail',
            'doc_type': 'document',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Insufficient tokens')
        self.assertEqual(UploadedDocument.objects.filter(title='Should Fail').count(), 0)

    def test_document_detail_api(self):
        doc = UploadedDocument.objects.create(
            user=self.user,
            title='Doc Detail Test',
            original_filename='file.pdf',
            doc_type='receipt',
            status='completed',
            json_output={'key': 'value'},
            sql_output='SELECT 1;'
        )
        response = self.client.get(f'/documents/{doc.id}/detail/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'Doc Detail Test')
        self.assertEqual(data['json_output'], {'key': 'value'})
        self.assertEqual(data['sql_output'], 'SELECT 1;')

    def test_download_outputs(self):
        doc = UploadedDocument.objects.create(
            user=self.user,
            title='Download Test',
            original_filename='file.txt',
            status='completed',
            json_output={'invoice': 100},
            sql_output='INSERT INTO test VALUES (1);'
        )
        # Test JSON download
        json_resp = self.client.get(f'/documents/{doc.id}/download-output/json/')
        self.assertEqual(json_resp.status_code, 200)
        self.assertIn('application/json', json_resp['Content-Type'])

        # Test SQL download
        sql_resp = self.client.get(f'/documents/{doc.id}/download-output/sql/')
        self.assertEqual(sql_resp.status_code, 200)
        self.assertIn('INSERT INTO', sql_resp.content.decode())

    def test_credit_topup_view(self):
        credit = UserCredit.objects.get(user=self.user)
        initial = credit.tokens
        response = self.client.post('/credits/topup/', {'amount': 50}, follow=True)
        self.assertEqual(response.status_code, 200)
        credit.refresh_from_db()
        self.assertEqual(credit.tokens, initial + 50)

    def test_external_system_apis(self):
        # Create a pending document
        doc = UploadedDocument.objects.create(
            user=self.user,
            title='Pending For Worker',
            original_filename='pending.png',
            doc_type='invoice',
            status='pending',
        )

        # 1. External system polls pending documents
        poll_resp = self.client.get('/api/documents/pending/')
        self.assertEqual(poll_resp.status_code, 200)
        poll_data = poll_resp.json()
        self.assertGreaterEqual(poll_data['pending_count'], 1)
        self.assertTrue(any(d['id'] == doc.id for d in poll_data['documents']))

        # 2. External system submits converted results
        submit_payload = {
            'status': 'completed',
            'extracted_text': 'EXTERNAL OCR TEXT: INVOICE #9988',
            'json_output': {'invoice_num': '9988', 'total': 1200.00},
            'sql_output': 'INSERT INTO invoices (id) VALUES (9988);'
        }
        submit_resp = self.client.post(
            f'/api/documents/{doc.id}/submit-result/',
            data=json.dumps(submit_payload),
            content_type='application/json'
        )
        self.assertEqual(submit_resp.status_code, 200)

        # Verify document updated in DB
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'completed')
        self.assertEqual(doc.extracted_text, 'EXTERNAL OCR TEXT: INVOICE #9988')
        self.assertEqual(doc.json_output['invoice_num'], '9988')
