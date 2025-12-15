module.exports = {
    database: {
        host: process.env.DB_HOST || '8.222.170.22',
        port: process.env.DB_PORT || 5432,
        database: process.env.DB_NAME || 'urlshortener',
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || 'postgres'
    },
    port: process.env.PORT || 4000
};