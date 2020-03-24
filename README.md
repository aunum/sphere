# Sphere

API based reinforcement learning environments.

## Overview

Sphere provides HTTP+gRPC interfaces for reinforcement learning environments. It grants a common 
abstraction for RL backends that is accessible from any language. 

### Current Backends  
* [Gym](./cmd/env/gym)

## API
The API definitions are found in the [api package](./api).

## Examples

There is a test example in [test/cartpole](./test/cartpole), there are many examples in [github.com/aunum/gold](http://github.com/aunum/gold).

## Contibuting
Please open an issue for any features/issues with the project.

To generate the API files
```
make generate
```

To build the server images
```
make build
```

## Roadmap
- [ ] Support more language types (s4tf, rust, nim, julia, c)
- [ ] Web frontend
- [ ] Unity backend
- [ ] Multi-agent
- [ ] ONNX tensors

## Inspiration
- [OpenAI Gym](https://gym.openai.com/)
- [Ray](https://github.com/ray-project/ray)
