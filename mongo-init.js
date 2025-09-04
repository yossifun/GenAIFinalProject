// MongoDB initialization script for SMS Chatbot
// This script runs when the MongoDB container starts for the first time

// Switch to the sms_chatbot database
db = db.getSiblingDB('sms_chatbot');

// Create collections
db.createCollection('users');
db.createCollection('conversations');

// Create indexes for better performance
db.users.createIndex({ "phone_number": 1 }, { unique: true });
db.conversations.createIndex({ "phone_number": 1 });
db.conversations.createIndex({ "timestamp": 1 });

// Insert some sample data for testing
db.users.insertOne({
    phone_number: "5551234567",
    job_interest: "Python Developer",
    conversation_summary: "Sample user for testing purposes",
    created_at: new Date(),
    last_updated: new Date()
});

print("MongoDB initialization completed successfully!");
print("Database: sms_chatbot");
print("Collections: users, conversations");
print("Indexes created for phone_number and timestamp"); 