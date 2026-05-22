#!/bin/bash
# =====================================================
# AWS Lambda Deployment Script
# Universal RAG System Backend
# =====================================================

set -e

FUNCTION_NAME="universal-rag-api"
REGION="ap-south-1"  # Mumbai region (change if needed)
PACKAGE_DIR="lambda_package"
ZIP_FILE="lambda_deployment.zip"

echo "=========================================="
echo "  Universal RAG System - Lambda Deploy"
echo "=========================================="

# Step 1: Clean previous build
echo "[1/5] Cleaning previous build..."
rm -rf $PACKAGE_DIR $ZIP_FILE

# Step 2: Install dependencies into package directory
echo "[2/5] Installing dependencies..."
mkdir -p $PACKAGE_DIR
pip install -r requirements-lambda.txt -t $PACKAGE_DIR --quiet --no-cache-dir

# Step 3: Copy backend code
echo "[3/5] Copying backend code..."
cp -r backend $PACKAGE_DIR/backend

# Step 4: Create ZIP
echo "[4/5] Creating deployment package..."
cd $PACKAGE_DIR
zip -r ../$ZIP_FILE . -q
cd ..

ZIP_SIZE=$(du -sh $ZIP_FILE | cut -f1)
echo "    Package size: $ZIP_SIZE"

# Step 5: Deploy to Lambda
echo "[5/5] Deploying to AWS Lambda..."

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "    Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://$ZIP_FILE \
        --region $REGION
else
    echo "    Function not found. Create it first using the AWS Console or run:"
    echo ""
    echo "    aws lambda create-function \\"
    echo "      --function-name $FUNCTION_NAME \\"
    echo "      --runtime python3.11 \\"
    echo "      --handler backend.main.handler \\"
    echo "      --role arn:aws:iam::<ACCOUNT_ID>:role/lambda-execution-role \\"
    echo "      --zip-file fileb://$ZIP_FILE \\"
    echo "      --timeout 30 \\"
    echo "      --memory-size 512 \\"
    echo "      --region $REGION \\"
    echo "      --environment Variables='{SECRET_KEY=your-secret,GROQ_API_KEY=your-key}'"
    echo ""
    exit 1
fi

# Cleanup
rm -rf $PACKAGE_DIR

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Next: Set up API Gateway to trigger this Lambda"
echo "Handler: backend.main.handler"
