import * as React from 'react';
import { useEffect } from 'react';
import { Dialog, DialogClose, DialogContent, DialogTitle, DialogTrigger } from '@/components/ui/dialog.tsx';
import { IconX } from '@tabler/icons-react';
import { ImageOff } from 'lucide-react';
import { cn } from '@/lib/utils.ts';
import { Spinner } from '@/components/ui/spinner.tsx';
import { ItemType } from '@/lib/types.ts';

export const PreviewImage = ({
  imageUrl,
  item,
  className,
}: {
  imageUrl: string;
  item: ItemType | null;
  className?: string;
}) => {
  const [isLoaded, setIsLoaded] = React.useState<boolean | null>(null); // null for loading in progress, true for success, false for failure
  const urlObject = new URL('/content/fetch-image', window.location.origin);
  urlObject.searchParams.set('image-url', encodeURI(imageUrl));

  if (item) {
    urlObject.searchParams.set('item-id', item.id);
    urlObject.searchParams.set('cache-key', item.updated_at);
  }

  const imageLocalURL = urlObject.toString();

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoaded(null);
  }, [imageUrl]);

  return (
    <div className="group item__image-container relative">
      {isLoaded === null && (
        <div
          className={cn(
            className,
            'item__image flex min-h-16 min-w-16 animate-pulse items-center justify-center bg-gray-100'
          )}
        >
          <Spinner className="text-muted-foreground size-6" />
        </div>
      )}
      {isLoaded === false && (
        <div
          className={cn(
            className,
            'text-muted-foreground item__image flex min-h-16 min-w-16 items-center justify-center bg-gray-200'
          )}
          title={`Image link is broken: ${imageUrl}`}
        >
          <ImageOff />
        </div>
      )}
      <Dialog>
        <DialogTrigger asChild>
          <img
            className={cn(className, 'item__image', isLoaded ? '' : 'hidden')}
            src={imageLocalURL}
            title={imageUrl}
            onLoad={() => {
              setIsLoaded(true);
            }}
            onError={() => {
              setIsLoaded(false);
            }}
          />
        </DialogTrigger>
        <DialogContent
          aria-describedby={undefined}
          showCloseButton={false}
          className="w-max border-0 bg-transparent p-0 shadow-none"
        >
          <DialogTitle className="hidden">Image Preview</DialogTitle>
          <DialogClose asChild>
            <button
              type="button"
              className="bg-background hover:bg-accent absolute -top-4 -right-4 rounded-full p-2 shadow transition"
              aria-label="Close"
            >
              <IconX size={20} />
            </button>
          </DialogClose>
          <img
            className={cn('h-auto max-h-[90vh] object-contain', imageUrl.endsWith('.svg') ? 'w-[500px]' : 'w-auto')}
            src={imageLocalURL}
            title={imageUrl}
            alt={'Preview of image: ' + imageUrl}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};
