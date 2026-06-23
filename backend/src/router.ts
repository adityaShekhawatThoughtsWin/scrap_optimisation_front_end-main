// src/routes.ts
import { Router, Request, Response } from 'express';
import UploadRouter from './modules/upload/upload.router';
import ModelRouter from './modules/model/model.router';
import { ROUTES} from './constants/route';
import DownloadRouter from './modules/download/download.router';

const apiRouter = Router();

// Health check endpoint for monitoring systems and uptime checks
apiRouter.get(ROUTES.API_HEALTH, (req: Request, res: Response) => {
  res.status(200).json({ 
    status: 'UP', 
    timestamp: new Date().toISOString() 
  });
});

apiRouter.use(ROUTES.UPLOAD_ROOT, UploadRouter)
apiRouter.use(ROUTES.MODEL_ROOT, ModelRouter)
apiRouter.use(ROUTES.DOWNLOAD_ROOT, DownloadRouter)

export default apiRouter;
