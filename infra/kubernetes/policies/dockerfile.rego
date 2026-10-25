# ERP03 Dockerfile policy rules (conftest)
deny[msg] {
    input.Dockerfile
    not contains(input.Dockerfile, "USER ")
    msg := "Dockerfile does not switch to a non-root USER"
}

deny[msg] {
    input.Dockerfile
    contains(input.Dockerfile, "ADD ")
    not contains(input.Dockerfile, "COPY ")
    msg := "Dockerfile uses ADD; prefer COPY for better cache control"
}

warn[msg] {
    input.Dockerfile
    contains(input.Dockerfile, "latest")
    msg := "Dockerfile references the 'latest' image tag; pin a specific digest"
}
