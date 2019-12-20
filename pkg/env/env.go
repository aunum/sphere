package env

import (
	"context"
	"fmt"
	"log"

	"github.com/ory/dockertest"
	sphere "github.com/pbarker/sphere/api/gen/go/v1alpha"
	"google.golang.org/grpc"
)

// Server of environments.
type Server struct {
	// Client to connect to the Sphere server.
	Client sphere.EnvironmentAPIClient
}

// ServerConfig is the environment server config.
type ServerConfig struct {
	// Docker image of environment.
	Image string
	// Version of the docker image.
	Version string
	// Port the environment is exposed on.
	Port string
}

// GymServerConfig is a configuration for a OpenAI Gym server environment.
var GymServerConfig = &ServerConfig{Image: "sphereproject/gym", Version: "latest", Port: "50051/tcp"}

// NewLocalServer creates a new environment server by launching a docker container and connecting to it.
func NewLocalServer(config *ServerConfig) (*Server, error) {
	pool, err := dockertest.NewPool("")
	if err != nil {
		return nil, fmt.Errorf("Could not connect to docker: %s", err)
	}

	resource, err := pool.Run(config.Image, config.Version, []string{})
	if err != nil {
		return nil, fmt.Errorf("Could not start resource: %s", err)
	}

	var sphereClient sphere.EnvironmentAPIClient

	// exponential backoff-retry, because the application in the container might not be ready to accept connections yet
	if err := pool.Retry(func() error {
		var err error
		address := fmt.Sprintf("localhost:%s", resource.GetPort(config.Port))
		conn, err := grpc.Dial(address, grpc.WithInsecure(), grpc.WithBlock())
		if err != nil {
			return err
		}
		defer conn.Close()
		fmt.Println("connected!")
		sphereClient = sphere.NewEnvironmentAPIClient(conn)
		resp, err := sphereClient.Info(context.Background(), &sphere.Empty{})
		fmt.Println(resp)
		return err
	}); err != nil {
		log.Fatalf("Could not connect to docker: %s", err)
	}

	return &Server{
		Client: sphereClient,
	}, nil
}

// Env is a convienience environment wrapper.
type Env struct {
	model string
	ID    string
}

// Make an environment.
func (s *Server) Make(model string) (*Env, error) {
	ctx := context.Background()
	resp, err := s.Client.CreateEnv(ctx, &sphere.CreateEnvRequest{ModelName: model})
	if err != nil {
		return nil, err
	}
	log.Printf("created env: %s \n", resp.Id)
	rresp, err := s.Client.StartRecordEnv(ctx, &sphere.StartRecordEnvRequest{Id: resp.Id})
	if err != nil {
		return nil, err
	}
	log.Println(rresp.Message)
	return &Env{
		model: model,
		ID:    resp.Id,
	}, nil
}

// Step through the environment.
func (e *Env) Step() {

}
