package env

import (
	"context"
	"fmt"
	"log"

	"github.com/ory/dockertest"
	sphere "github.com/pbarker/sphere/api/gen/go/v1alpha"
	"google.golang.org/grpc"
)

// Env is a convienience environment wrapper.
type Env struct {
	modelName string
	record    bool
	ID        string
	Client    sphere.EnvironmentAPIClient
}

// NewLocalEnv creates a new environment by launching a docker container and connecting to it.
func NewLocalEnv(modelName string, record bool) (*Env, error) {
	pool, err := dockertest.NewPool("")
	if err != nil {
		return nil, fmt.Errorf("Could not connect to docker: %s", err)
	}

	resource, err := pool.Run("sphereproject/gym", "latest", []string{})
	if err != nil {
		return nil, fmt.Errorf("Could not start resource: %s", err)
	}

	var sphereClient sphere.EnvironmentAPIClient

	// exponential backoff-retry, because the application in the container might not be ready to accept connections yet
	if err := pool.Retry(func() error {
		var err error
		address := fmt.Sprintf("localhost:%s", resource.GetPort("50051/tcp"))
		conn, err := grpc.Dial(address, grpc.WithInsecure(), grpc.WithBlock())
		if err != nil {
			return err
		}
		defer conn.Close()
		sphereClient = sphere.NewEnvironmentAPIClient(conn)
		_, err = sphereClient.Info(context.Background(), nil)
		return err
	}); err != nil {
		log.Fatalf("Could not connect to docker: %s", err)
	}
	cresp, err := sphereClient.CreateEnv(context.Background(), &sphere.CreateEnvRequest{ModelName: modelName})
	if err != nil {
		return nil, err
	}
	log.Print(cresp)
	if record {
		rresp, err := sphereClient.StartRecordEnv(context.Background(), &sphere.StartRecordEnvRequest{})
		if err != nil {
			return nil, err
		}
		log.Print(rresp)
	}
	return &Env{
		modelName: modelName,
		record:    record,
		Client:    sphereClient,
	}, nil
}

// Step through the environment.
func (e *Env) Step() {

}
