serve:
	hupper -m app -w .

test_serve:
	DB_NAME=monkeymoney_test make serve

deploy:
	ssh monkeymoney '\
		cd ~/monkeymoney/api &&\
		git pull &&\
		pip install -r requirements.txt &&\
		sudo systemctl daemon-reload &&\
		sudo systemctl restart monkeymoney-api &&\
	echo "deployed!"'
