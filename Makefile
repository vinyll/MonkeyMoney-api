serve:
	hupper -m app -w .

test_serve:
	DB_NAME=monkeymoney_test make serve
