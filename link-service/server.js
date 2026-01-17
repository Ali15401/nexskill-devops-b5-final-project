const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const { Pool } = require('pg');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');

// AWS SDK imports
const { S3Client, PutObjectCommand, GetObjectCommand } = require('@aws-sdk/client-s3');
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');
const { CloudWatchClient, PutMetricDataCommand } = require('@aws-sdk/client-cloudwatch');
const { SSMClient, GetParameterCommand } = require('@aws-sdk/client-ssm');

const app = express();
const port = process.env.PORT || 5001;
const region = process.env.AWS_REGION || 'us-east-1';

// AWS clients configuration
const s3Client = new S3Client({ region });
const secretsClient = new SecretsManagerClient({ region });
const cloudwatchClient = new CloudWatchClient({ region });
const ssmClient = new SSMClient({ region });

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Multer configuration for file uploads
const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 10 * 1024 * 1024 } // 10MB limit
});

// Initialize the database
let pool;

async function initializeDatabase() {
    try {
        console.log('Fetching database credentials from AWS Secrets Manager...');
        const data = await secretsClient.send(
            new GetSecretValueCommand({ SecretId: 'YOUR_SECRET_NAME' })
        );
        const credentials = JSON.parse(data.SecretString);
        pool = new Pool({
            host: credentials.host,
            port: credentials.port,
            database: credentials.dbname,
            user: credentials.username,
            password: credentials.password
        });
        console.log('Database connection established.');
    } catch (error) {
        console.error('Database initialization error:', error.message);
        throw error;
    }
}

// Health Check Route
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date() });
});

// File Upload Route
app.post('/upload', upload.single('file'), async (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }

    const fileKey = `uploads/${uuidv4()}-${req.file.originalname}`;
    try {
        const uploadParams = {
            Bucket: 'YOUR_BUCKET_NAME',
            Key: fileKey,
            Body: req.file.buffer,
            ContentType: req.file.mimetype
        };

        await s3Client.send(new PutObjectCommand(uploadParams));
        res.json({ fileKey, message: 'Upload successful' });
    } catch (error) {
        console.error('File upload error:', error.message);
        res.status(500).json({ error: 'File upload failed' });
    }
});

// Start server
initializeDatabase().then(() => {
    app.listen(port, () => {
        console.log(`Server running on port ${port}`);
    });
}).catch(err => {
    console.error('Failed to start server:', err.message);
    process.exit(1);
});
