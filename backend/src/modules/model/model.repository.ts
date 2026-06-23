import { prisma } from "../../lib/prisma";

export class ModelRepository {
  getFilesByIds = async (ids: number[]) => {
    return prisma.data.findMany({
      where: {
        id: { in: ids },
      },
    });
  };
}