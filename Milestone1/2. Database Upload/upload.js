require('dotenv').config();  // Load environment variables from the .env file
const cloudinary = require('cloudinary').v2;
const fs = require('fs');
const path = require('path');

// Log Cloudinary credentials for debugging
console.log('Cloudinary Cloud Name:', process.env.CLOUDINARY_CLOUD_NAME);

// Configure Cloudinary with your credentials
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

// Function to upload a single image to Cloudinary
const uploadImage = (imagePath, folder) => {
  const fileName = path.basename(imagePath, path.extname(imagePath));
  return new Promise((resolve, reject) => {
    cloudinary.uploader.upload(imagePath, { folder: folder, public_id: fileName }, (error, result) => {
      if (error) {
        reject(error);
      } else {
        resolve(result);
      }
    });
  });
};

// Upload images from a specific folder
const uploadImagesFromFolder = async (folderPath, cloudFolder) => {
  const files = fs.readdirSync(folderPath);

  console.log("Files in folder:", files);  // Debugging: Check the files in the folder

  // Filter only image files (you can add more extensions if needed)
  const imageFiles = files.filter(file => ['.jpg', '.jpeg', '.png', '.gif'].includes(path.extname(file).toLowerCase()));

  // Loop through each image and upload
  for (let i = 0; i < imageFiles.length; i++) {
    const imagePath = path.join(folderPath, imageFiles[i]);
    console.log(`Uploading: ${imageFiles[i]} to Cloudinary folder: ${cloudFolder}`);

    try {
      const result = await uploadImage(imagePath, cloudFolder);
      console.log(`Uploaded: ${result.secure_url}`);
    } catch (error) {
      console.error(`Failed to upload ${imageFiles[i]}: ${error.message}`);
    }
  }
};

// Path to the local folders containing your image datasets
const folderPath1 = '../1.  Web Scraping (Using Bing Image Downloader)/financial_data/bank_statements';  // Local folder for bank statements
const folderPath2 = '../1.  Web Scraping (Using Bing Image Downloader)/financial_data/cheques';  // Local folder for cheques
const folderPath3 = '../1.  Web Scraping (Using Bing Image Downloader)/financial_data/profit_loss_statements';  // Local folder for profit loss statements
const folderPath4 = '../1.  Web Scraping (Using Bing Image Downloader)/financial_data/salary_slips' // Local folder for salary slips
const folderPath5 = '../1.  Web Scraping (Using Bing Image Downloader)/financial_data/transaction_history' // Local folder for transaction history

// Start uploading the images to the corresponding Cloudinary folders
uploadImagesFromFolder(folderPath1, 'financial_data/bank_statements');
uploadImagesFromFolder(folderPath2, 'financial_data/cheques');
uploadImagesFromFolder(folderPath3, 'financial_data/profit_loss_statements');
uploadImagesFromFolder(folderPath4, 'financial_data/salary_slips');
uploadImagesFromFolder(folderPath5, 'financial_data/transaction_history');