import io
import re
import unittest
from unittest.mock import patch
from parameterized import parameterized
import app

DOC_FIXTURES = [
    ('TESTDOC', 'TESTDOC-1', 'TESTUSER-1', 'TESTSHELF-1', 'TESTSHELF-2')
]


class TestFunctions(unittest.TestCase):
    def setUp(self):
        app.directories = {}
        app.documents = []

    @patch('builtins.input', create=True)
    def call_function_mocked_input(self, function, input_vars: list, *args, **kwargs):
        """
        :param function: function to call
        :param input_vars: values to be passed to the input request
        :param args: arguments passed to the function
        :param kwargs: kwargs passed to the function
        :return: the result of the passed function
        """
        args = list(args)
        mocked_input = args.pop()
        mocked_input.side_effect = input_vars
        return function(*args, **kwargs)

    @parameterized.expand(DOC_FIXTURES)
    def test_add_new_shelf(self, _, __, ___, ____, new_shelf_number):
        shelf_number, result = app.add_new_shelf(new_shelf_number)
        self.assertTrue(result and shelf_number in app.directories)
        self.assertEqual(shelf_number, new_shelf_number)

    @parameterized.expand(DOC_FIXTURES)
    def test_add_new_doc(self, doc_type, number, holder, shelf_number, *args):
        self.assertEqual(
            self.call_function_mocked_input(app.add_new_doc, [number, doc_type, holder, shelf_number]),
            shelf_number
        )
        self.assertTrue(shelf_number in app.directories and number in app.directories.get(shelf_number))
        self.assertEqual(app.documents, [{
            'type': doc_type,
            'number': number,
            'name': holder
        }])

    @parameterized.expand(DOC_FIXTURES)
    def test_check_document_existance(self, doc_type, number, holder, *args):
        app.documents = [{'type': doc_type, 'number': number, 'name': holder}]
        self.assertTrue(app.check_document_existance(number))

    @parameterized.expand(DOC_FIXTURES)
    def test_get_doc_owner_name(self, doc_type, number, holder, *args):
        app.documents = [{'type': doc_type, 'number': number, 'name': holder}]
        self.assertEqual(
            self.call_function_mocked_input(app.get_doc_owner_name, [number]),
            holder
        )

    @parameterized.expand(DOC_FIXTURES)
    def test_remove_doc_from_shelf(self, doc_type, number, holder, shelf_number, *args):
        app.documents = [{'type': doc_type, 'number': number, 'name': holder}]
        app.directories = {shelf_number: [number]}
        self.assertIsNone(app.remove_doc_from_shelf(number))
        self.assertFalse(number in app.directories.get(shelf_number))

    @parameterized.expand(DOC_FIXTURES)
    def test_get_doc_shelf(self, doc_type, number, holder, shelf_number, *args):
        app.documents = [{'type': doc_type, 'number': number, 'name': holder}]
        app.directories = {shelf_number: [number]}
        result = self.call_function_mocked_input(app.get_doc_shelf, [number])
        self.assertEqual(result, shelf_number)

    @parameterized.expand(DOC_FIXTURES)
    def test_append_doc_to_shelf(self, doc_type, number, holder, shelf_number, *args):
        app.documents = [{'type': doc_type, 'number': number, 'name': holder}]
        self.assertIsNone(app.append_doc_to_shelf(number, shelf_number))
        self.assertTrue(number in app.directories.get(shelf_number))

    @parameterized.expand(DOC_FIXTURES)
    def test_move_doc_to_shelf(self, doc_type, number, holder, shelf_number, new_shelf_number):
        app.documents = [{'type': doc_type, 'number': number, 'name': holder}]
        app.directories = {shelf_number: [number]}
        result = self.call_function_mocked_input(app.move_doc_to_shelf, [number, new_shelf_number])
        self.assertIsNone(result)
        self.assertFalse(number in app.directories.get(shelf_number))
        self.assertTrue(number in app.directories.get(new_shelf_number))

    @parameterized.expand(DOC_FIXTURES)
    def test_delete_doc(self, doc_type, number, holder, shelf_number, *args):
        app.documents = [{'type': doc_type, 'number': number, 'name': holder}]
        app.directories = {shelf_number: [number]}
        doc_number, result = self.call_function_mocked_input(app.delete_doc, [number])
        self.assertEqual(doc_number, number)
        self.assertTrue(result)
        self.assertFalse(number in app.directories.get(shelf_number))
        self.assertEqual(app.documents, [])

    @parameterized.expand(DOC_FIXTURES)
    def test_get_all_doc_owners_names(self, doc_type, number, holder, shelf_number, *args):
        app.documents = [{'type': doc_type, 'number': number, 'name': holder}]
        self.assertTrue(holder in app.get_all_doc_owners_names())

    @patch('builtins.input', create=True)
    def test_secretary_program_start(self, mocked_input):
        doc_type, number, holder, shelf_number, new_shelf_number = DOC_FIXTURES[0]
        # command as: must add a shelf
        mocked_input.side_effect = ['as', new_shelf_number, 'q']
        app.secretary_program_start()
        self.assertTrue(new_shelf_number in app.directories)
        # command a: must add a document
        mocked_input.side_effect = ['a', number, doc_type, holder, shelf_number, 'q']
        app.secretary_program_start()
        self.assertTrue(number in app.directories.get(shelf_number))
        self.assertEqual(app.documents, [{'type': doc_type, 'number': number, 'name': holder}])
        # command s: displays the shelf number by document number
        mocked_input.side_effect = ['s', number, 'q']
        with patch('sys.stdout', new=io.StringIO()) as stdout:
            app.secretary_program_start()
        self.assertTrue(re.search(r"\b" + shelf_number + r"\b", stdout.getvalue()))
        # command m: moves the document to another shelf
        mocked_input.side_effect = ['m', number, new_shelf_number, 'q']
        app.secretary_program_start()
        self.assertFalse(number in app.directories.get(shelf_number))
        self.assertTrue(number in app.directories.get(new_shelf_number))
        # command ap: displays a set of all document owners
        mocked_input.side_effect = ['ap', 'q']
        with patch('sys.stdout', new=io.StringIO()) as stdout:
            app.secretary_program_start()
        self.assertTrue(re.search(f"{{'{holder}'}}", stdout.getvalue()))
        # command p: displays the owner by document number
        mocked_input.side_effect = ['p', number, 'q']
        with patch('sys.stdout', new=io.StringIO()) as stdout:
            app.secretary_program_start()
        self.assertTrue(re.search(holder, stdout.getvalue()))
        # command l: displays a list of documents
        mocked_input.side_effect = ['l', 'q']
        with patch('sys.stdout', new=io.StringIO()) as stdout:
            app.secretary_program_start()
        self.assertTrue(re.search(f'{doc_type} "{number}" "{holder}"\n', stdout.getvalue()))
        # command d: deletes a document
        mocked_input.side_effect = ['d', number, 'q']
        app.secretary_program_start()
        self.assertFalse(number in app.directories.get(new_shelf_number))
        self.assertEqual(app.documents, [])
