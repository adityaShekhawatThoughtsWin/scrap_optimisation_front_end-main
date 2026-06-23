import { prisma } from "../../lib/prisma";
import { FileType } from "../../constants/types";

export class UploadRepository {
  createUploadRecord = async (filepath: string, uploadType: FileType) => {
    return prisma.data.create({
      data: {
        filepath,
        upload_type: uploadType,
      },
    });
  };

  getById = async (id: number) => {
    return prisma.data.findUnique({
      where: { id },
    });
  };
}