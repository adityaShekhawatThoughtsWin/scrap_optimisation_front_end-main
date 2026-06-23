import { prisma } from "../../lib/prisma";
import { FileType } from "../../constants/types";

export class DownloadRepository {
  getLatestByType = async (uploadType: FileType) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return prisma.data.findFirst({
      where: {
        upload_type: uploadType,
        is_deleted: false,
        created_at: {
          lt: today,
        },
      },
      orderBy: {
        created_at: "desc",
      },
    });
  };
}