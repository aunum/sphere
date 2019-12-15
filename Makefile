
generate:
	docker run --rm -it -v "$$PWD:/go/src/github.com/pbarker/sphere" "$$(docker build -f Dockerfile.gen --quiet .)" prototool lint
	docker run --rm -it -v "$$PWD:/go/src/github.com/pbarker/sphere" "$$(docker build -f Dockerfile.gen --quiet .)" prototool generate