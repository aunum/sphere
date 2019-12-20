package env

import (
	"context"
	"fmt"
	"testing"

	sphere "github.com/pbarker/sphere/api/gen/go/v1alpha"
	"github.com/stretchr/testify/require"
	"google.golang.org/grpc"
)

// func TestLocal(t *testing.T) {
// 	server, err := NewLocalServer(GymServerConfig)
// 	require.Nil(t, err)
// 	env, err := server.Make("CartPole-v0")
// 	require.Nil(t, err)
// 	fmt.Println(env)
// }

func TestLocal(t *testing.T) {
	address := fmt.Sprintf("localhost:%s", "50051")
	conn, err := grpc.Dial(address, grpc.WithInsecure(), grpc.WithBlock())
	require.Nil(t, err)
	defer conn.Close()
	fmt.Println("connected!")
	sphereClient := sphere.NewEnvironmentAPIClient(conn)
	_, err = sphereClient.Info(context.Background(), &sphere.Empty{})
	require.Nil(t, err)

	server := Server{Client: sphereClient}
	env, err := server.Make("CartPole-v0")
	require.Nil(t, err)
	fmt.Println(env)
}
