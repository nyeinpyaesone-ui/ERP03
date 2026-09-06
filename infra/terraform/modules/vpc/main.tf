# VPC Module for ERP Infrastructure
variable "environment" { type = string }
variable "vpc_cidr" { type = string; default = "10.0.0.0/16" }
variable "availability_zones" { type = list(string); default = ["ap-southeast-1a", "ap-southeast-1b", "ap-southeast-1c"] }
variable "single_nat_gateway" { type = bool; default = false }

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support = true
  tags = { Name = "erp-${var.environment}-vpc", Environment = var.environment, ManagedBy = "terraform" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "erp-${var.environment}-igw", Environment = var.environment }
}

resource "aws_subnet" "public" {
  count = length(var.availability_zones)
  vpc_id = aws_vpc.main.id
  cidr_block = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  tags = { Name = "erp-${var.environment}-public-${count.index}", Type = "public" }
}

resource "aws_subnet" "private" {
  count = length(var.availability_zones)
  vpc_id = aws_vpc.main.id
  cidr_block = cidrsubnet(var.vpc_cidr, 8, count.index + 3)
  availability_zone = var.availability_zones[count.index]
  tags = { Name = "erp-${var.environment}-private-${count.index}", Type = "private" }
}

resource "aws_eip" "nat" {
  count = var.single_nat_gateway ? 0 : length(var.availability_zones)
  domain = "vpc"
  tags = { Name = "erp-${var.environment}-nat-eip-${count.index}" }
}

resource "aws_nat_gateway" "main" {
  count = var.single_nat_gateway ? 0 : length(var.availability_zones)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id = aws_subnet.public[count.index].id
  tags = { Name = "erp-${var.environment}-nat-${count.index}" }
  depends_on = [aws_internet_gateway.main]
}

resource "aws_eip" "nat_single" {
  count = var.single_nat_gateway ? 1 : 0
  domain = "vpc"
}

resource "aws_nat_gateway" "nat_single" {
  count = var.single_nat_gateway ? 1 : 0
  allocation_id = aws_eip.nat_single[0].id
  subnet_id = aws_subnet.public[0].id
  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route { cidr_block = "0.0.0.0/0"; gateway_id = aws_internet_gateway.main.id }
  tags = { Name = "erp-${var.environment}-public-rt" }
}

resource "aws_route_table" "private" {
  count = var.single_nat_gateway ? 0 : length(var.availability_zones)
  vpc_id = aws_vpc.main.id
  route { cidr_block = "0.0.0.0/0"; nat_gateway_id = aws_nat_gateway.main[count.index].id }
  tags = { Name = "erp-${var.environment}-private-rt-${count.index}" }
}

resource "aws_route_table" "private_single" {
  count = var.single_nat_gateway ? 1 : 0
  vpc_id = aws_vpc.main.id
  route { cidr_block = "0.0.0.0/0"; nat_gateway_id = aws_nat_gateway.nat_single[0].id }
  tags = { Name = "erp-${var.environment}-private-rt" }
}

resource "aws_route_table_association" "public" {
  count = length(var.availability_zones)
  subnet_id = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = var.single_nat_gateway ? 0 : length(var.availability_zones)
  subnet_id = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "private_single" {
  count = var.single_nat_gateway ? length(var.availability_zones) : 0
  subnet_id = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private_single[0].id
}

output "vpc_id" { value = aws_vpc.main.id }
output "public_subnet_ids" { value = aws_subnet.public[*].id }
output "private_subnet_ids" { value = aws_subnet.private[*].id }
output "availability_zones" { value = var.availability_zones }
