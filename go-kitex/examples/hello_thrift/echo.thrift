namespace go echo

struct EchoRequest {
    1: required string message
    2: optional string request_id
}

struct EchoResponse {
    1: required string message
}

service EchoService {
    EchoResponse Echo(1: EchoRequest req)
}
