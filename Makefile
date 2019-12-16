
generate:
	docker run --rm -it -v "$$PWD:/go/src/github.com/pbarker/sphere" "$$(docker build -f Dockerfile.gen --quiet .)" prototool lint
	docker run --rm -it -v "$$PWD:/go/src/github.com/pbarker/sphere" "$$(docker build -f Dockerfile.gen --quiet .)" prototool generate
	# TODO: build binary plugins
	docker run --rm -it -v "$$PWD:/go/src/github.com/pbarker/sphere" "$$(docker build -f Dockerfile.gen --quiet .)" python -m grpc.tools.protoc --python_out=./api/gen/python/v1alpha --grpc_python_out=./api/gen/python/v1alpha --proto_path ./api/v1alpha --proto_path /go/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis env.proto